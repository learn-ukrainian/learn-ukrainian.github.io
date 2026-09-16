"""Curated heteronym dataset (Batch 9) for Word Atlas (#8039, #4387).

This module defines 32 curated heteronym lemmas (64 distinct variants)
expanding the curated heteronym SSOT from 264 to 296 lemmas.

Decolonization & Lexicographical Invariants:
1. Modern standard baseline: Academic СУМ-20 / ВТС / ULIF authorities.
2. Authentic pre-Soviet witness: Грінченко (1907–1909), compiled/published
   under Tsarist Russian imperial bans (Valuev Circular 1863, Ems Ukaz 1876).
3. Soviet colonization context: СУМ-11 (1970–1980) documented transparently
   under `soviet_colonization_context` with `sovietization_risk` and historical notes
   without erasing lexical history. All quotations are 100% contiguous verbatim excerpts
   from academic sources.
4. Clean morphology and phonology: Every variant is morphologically verified against VESUM where present.
"""

from typing import Any

CURATED_HETERONYMS_BATCH_9: dict[str, list[dict[str, Any]]] = {'лупання': [{'headword': 'лу́пання',
              'short_label': 'кліпання, моргання очима (розм.)',
              'gloss': 'blinking, fluttering or popping of eyelids (colloquial)',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈlupɐnʲːɐ]'},
              'stress': {'form': 'лу́пання',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/лупання'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'середній',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'лу́пання',
                                                                 'plural': 'лу́пання'},
                                                    'родовий': {'singular': 'лу́пання',
                                                                'plural': 'лу́пань'},
                                                    'давальний': {'singular': 'лу́панню',
                                                                  'plural': 'лу́панням'},
                                                    'знахідний': {'singular': 'лу́пання',
                                                                  'plural': 'лу́пання'},
                                                    'орудний': {'singular': 'лу́панням',
                                                                'plural': 'лу́паннями'},
                                                    'місцевий': {'singular': 'лу́панні',
                                                                 'plural': 'лу́паннях'},
                                                    'кличний': {'singular': 'лу́пання',
                                                                'plural': 'лу́пання'}}}},
              'distinction_note': 'Означає дію за значенням дієслова «лу́пати» (моргати, кліпати '
                                  'очима). Не плутати з «лупа́ння» (дія за значенням «лупа́ти» — '
                                  'здирання кори чи відколювання каменю або руди).',
              'meaning': {'definitions': ['Дія за значенням лу́пати: швидке кліпання, моргання '
                                          'очима.'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ЛУ́ПАННЯ, я, с., фам. Дія за знач. '
                                                            'лу́пати. Пристрасть завертала йому '
                                                            'голову, а він давав приміту тої '
                                                            'пристрасті лиш лупанням очей і сумом '
                                                            '(Март., Тв., 1954, 257). ЛУПА́ННЯ, я, '
                                                            'с. Дія за знач. лупа́ти.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'ЛУпання, -ня, с. Миганіе (хлопаніе глазами).',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}},
             {'headword': 'лупа́ння',
              'short_label': 'здирання, відколювання, видобуток породи',
              'gloss': 'peeling, husking, chipping or quarrying of rock/ore',
              'pos': 'noun',
              'cefr': 'B1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[luˈpɑnʲːɐ]'},
              'stress': {'form': 'лупа́ння',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/лупання'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'середній',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'лупа́ння',
                                                                 'plural': 'лупа́ння'},
                                                    'родовий': {'singular': 'лупа́ння',
                                                                'plural': 'лупа́нь'},
                                                    'давальний': {'singular': 'лупа́нню',
                                                                  'plural': 'лупа́нням'},
                                                    'знахідний': {'singular': 'лупа́ння',
                                                                  'plural': 'лупа́ння'},
                                                    'орудний': {'singular': 'лупа́нням',
                                                                'plural': 'лупа́ннями'},
                                                    'місцевий': {'singular': 'лупа́нні',
                                                                 'plural': 'лупа́ннях'},
                                                    'кличний': {'singular': 'лупа́ння',
                                                                'plural': 'лупа́ння'}}}},
              'distinction_note': 'Означає дію за значенням дієслова «лупа́ти» (здирати '
                                  'шкаралупу/кору, розколювати каміння або добувати корисні '
                                  'копалини, як у Франковому «Каменярі»). Не плутати з «лу́пання» '
                                  '(кліпання очима).',
              'meaning': {'definitions': ['Дія за значенням лупа́ти: очищення від шкаралупи, '
                                          'відколювання пластів каменю, породи.'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ЛУПА́ННЯ, я, с. Дія за знач. лупа́ти. '
                                                            'У слюсарні біля Домсової фабрики '
                                                            'пищать і свищуть циркулярки, острячи '
                                                            '[гострячи] знаряди до лупання каменю '
                                                            '(Фр., VIII, 1952, 400).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'ЛупАння 2, -ня, с. Откалываніе, отламываніе.',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}}],
 'люстровий': [{'headword': 'лю́стровий',
                'short_label': "пов'язаний із підвісним світильником (люстрою)",
                'gloss': 'relating to a chandelier or suspended ceiling lamp',
                'pos': 'adj',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[ˈlʲustrɔwɪj]'},
                'stress': {'form': 'лю́стровий',
                           'source': 'ВТС / СУМ-11',
                           'url': 'https://slovnyk.me/dict/vts/люстровий'},
                'morphology': {'pos': 'прикметник',
                               'paradigm': {'kind': 'adjective',
                                            'forms': {'masculine': 'лю́стровий',
                                                      'feminine': 'лю́строва',
                                                      'neuter': 'лю́строве',
                                                      'plural': 'лю́строві'}}},
                'distinction_note': 'Означає «прикметник до лю́стра (підвісний освітлювальний '
                                    'прилад, світильник)». Не плутати з «люстро́вий» (люстриновий, '
                                    'з блискучої тканини; або дзеркальний від лю́стро).',
                'meaning': {'definitions': ["Прикметник до лю́стра: пов'язаний із підвісним "
                                            'світильником, люстровою лампою.'],
                            'source': 'ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ЛЮ́СТРОВИЙ, а, е. Прикм. до '
                                                              'лю́стра; // Підвісний (про лампу). '
                                                              'При використанні люстрових ламп '
                                                              'треба робити над ними захисні '
                                                              'козирки (Овоч. закр. і відкр. '
                                                              'грунту, 1957, 40). ЛЮСТРО́ВИЙ, а, '
                                                              'е, заст. Люстриновий.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної прозорості.'}},
               {'headword': 'люстро́вий',
                'short_label': 'люстриновий (з блискучої тканини) або дзеркальний',
                'gloss': 'made of lustrine (glossy woolen fabric) or mirror-like (archaic)',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[lʲuˈstrɔwɪj]'},
                'stress': {'form': 'люстро́вий',
                           'source': 'Грінченко (1907) / ВТС',
                           'url': 'https://slovnyk.me/dict/vts/люстровий'},
                'morphology': {'pos': 'прикметник',
                               'paradigm': {'kind': 'adjective',
                                            'forms': {'masculine': 'люстро́вий',
                                                      'feminine': 'люстро́ва',
                                                      'neuter': 'люстро́ве',
                                                      'plural': 'люстро́ві'}}},
                'distinction_note': 'Означає «виготовлений з люстрину (глянсової вовняної '
                                    'тканини)» або «дзеркальний (від лю́стро)». Не плутати з '
                                    "«лю́стровий» (пов'язаний із підвісною люстрою).",
                'meaning': {'definitions': ['Люстриновий (з глянсової тканини); дзеркальний.'],
                            'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ЛЮСТРО́ВИЙ, а, е, заст. '
                                                              'Люстриновий. Взяла очіпок '
                                                              'грезетовий, І кунтуш з усами '
                                                              'люстровий, Пішла к Зевесу на ралець '
                                                              '(Котл., І, 1952, 69).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної прозорості.'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'ЛюстрОвий, -а, -е. 1) Зеркальный. 2) Люстриновый. '
                                                'Взяла очіпок грезетовий і кунтуш з усами '
                                                'люстровий, пішла к Зевесу на ралець! Котл. Ен. І. '
                                                '12.',
                                       'historical_note': 'Автентичне народне мововживання, '
                                                          'зафіксоване Борисом Грінченком в умовах '
                                                          'дії антиукраїнських імперських указів '
                                                          '(Валуєвського циркуляра 1863 р. та '
                                                          'Емського указу 1876 р.).'}}],
 'маячний': [{'headword': 'мая́чний',
              'short_label': "пов'язаний із морським або річковим маяком",
              'gloss': 'beacon, lighthouse-related (e.g. lighthouse tower or marker crop)',
              'pos': 'adj',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[mɐˈjɑtʃnɪj]'},
              'stress': {'form': 'мая́чний',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/маячний'},
              'morphology': {'pos': 'прикметник',
                             'paradigm': {'kind': 'adjective',
                                          'forms': {'masculine': 'мая́чний',
                                                    'feminine': 'мая́чна',
                                                    'neuter': 'мая́чне',
                                                    'plural': 'мая́чні'}}},
              'distinction_note': "Означає «пов'язаний із маяком; маяковий (маячна башта, маячна "
                                  "культура)». Не плутати з «маячни́й» (гарячковий, пов'язаний із "
                                  'маренням та ма́ячнею).',
              'meaning': {'definitions': ["Те саме, що маяко́вий: пов'язаний із маяком, маячною "
                                          'баштою.'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'МАЯ́ЧНИЙ, а, е. Те саме, що '
                                                            'маяко́вий. Маячна башта. ∆ Мая́чна '
                                                            'культу́ра (росли́на) — культура, що '
                                                            'її висівають разом з іншими '
                                                            'культурами, але яка сходить раніше за '
                                                            'них і позначає рядки посівів. — '
                                                            'Колись було підсівали..',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}},
             {'headword': 'маячни́й',
              'short_label': 'гарячковий, викликаний маренням або ма́ячнею',
              'gloss': 'delirious, feverish, hallucinatory (relating to delirium or ravings)',
              'pos': 'adj',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[mɐjɐtʃˈnɪj]'},
              'stress': {'form': 'маячни́й',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/маячний'},
              'morphology': {'pos': 'прикметник',
                             'paradigm': {'kind': 'adjective',
                                          'forms': {'masculine': 'маячни́й',
                                                    'feminine': 'маячна́',
                                                    'neuter': 'маячне́',
                                                    'plural': 'маячні́'}}},
              'distinction_note': "Означає «пов'язаний із маяченням, гарячковим маренням (маячний "
                                  'стан, маячний сон)». Не плутати з «мая́чний» (маяковий, '
                                  "пов'язаний із сигнальним маяком).",
              'meaning': {'definitions': ['Стосовний до маячення, марення у хворобливому стані або '
                                          'безтямі.'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'МАЯЧНИ́Й, а́, е́. Стос. до маячення. '
                                                            'Та й усе життя отоді в Обухівці — не '
                                                            'віриться, що це була дійсність, а не '
                                                            'привиділось у важкому маячному сні '
                                                            '(Головко, II, 1957, 179); Неясні '
                                                            'маячні образи вимальовувались перед '
                                                            'ним (Ю.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}}],
 'набігати': [{'headword': 'набі́гати',
               'short_label': 'набути або напрацювати тривалим бігом (док.)',
               'gloss': 'acquire or suffer something through extensive running (perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐˈbiɦɐtɪ]'},
               'stress': {'form': 'набі́гати',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/набігати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «багато бігаючи, дістати щось або зазнати чогось '
                                   '(док.)». Не плутати з «набіга́ти» (недоконаний вид: '
                                   'насуватися, накочуватися, набігати на берег чи перешкоду).',
               'meaning': {'definitions': ['Багато бігаючи, дістати що-небудь або зазнати чогось '
                                           '(доконаний вид).'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАБІ́ГАТИ, аю, аєш, док., перех., '
                                                             'розм. Багато бігаючи, дістати '
                                                             'що-небудь або зазнати чогось. — Чи '
                                                             'не набігала ти.. лихоманки? '
                                                             '(Кв.-Осн., II, 1956, 325); // '
                                                             'Завагітніти (про неодружену жінку).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'НабІгати 1, -гаю, -єш, гл. Набегать, бегая '
                                               'получить. Набігав собі пранців.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}},
              {'headword': 'набіга́ти',
               'short_label': 'насуватися, накочуватися, напливати хвилями (недок.)',
               'gloss': 'rush onto, surge up, roll onto or sweep over (imperfective)',
               'pos': 'verb',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐbiˈɦɑtɪ]'},
               'stress': {'form': 'набіга́ти',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/набігати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': 'Означає «насуватися, накочуватися, напливати хвилями або '
                                   'набігом (недок. до набігти)». Не плутати з доконаним '
                                   '«набі́гати» (набути бігом).',
               'meaning': {'definitions': ['Наскакувати, натикатися з розбігу; насуватися, '
                                           'напливати (про хвилі, хмари, сльози).'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАБІГА́ТИ, а́ю, а́єш, недок., '
                                                             'НАБІ́ГТИ, біжу́, біжи́ш; мин. ч. '
                                                             'набі́г, ла, ло; док. 1. Наскакувати, '
                                                             'натикатися з розбігу, з розгону на '
                                                             'кого-, що-небудь. Вони набігали на '
                                                             'нас, штовхали, намагалися забити '
                                                             'памороки (10.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'НабігАти 2, -гАю, -єш, сов. в. набІгти, -біжУ, '
                                               '-жИш, гл. 1) Набегать, набежать.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}}],
 'набухати': [{'headword': 'набу́хати',
               'short_label': 'насипати, налити чи накидати багато (розм., док.)',
               'gloss': 'pour, heap or dump a large quantity of something (colloquial, perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐˈbuxɐtɪ]'},
               'stress': {'form': 'набу́хати',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/набухати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «накласти, накидати, налити багато чого-небудь (розм., '
                                   'док.)». Не плутати з «набуха́ти» (недоконаний вид: набрякати '
                                   'від вологи чи соків).',
               'meaning': {'definitions': ['Накласти, накидати або налити багато чого-небудь '
                                           '(розм., доконаний вид).'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАБУ́ХАТИ, аю, аєш, док., перех., '
                                                             'розм. 1. Накласти, накидати, налити '
                                                             'і т. ін. багато чого-небудь. '
                                                             'Набухали дров у піч. 2. Набити '
                                                             'кого-небудь, нанести удари комусь. '
                                                             'Набухали кулаками по спині. '
                                                             'НАБУХА́ТИ, а́є, недок., НАБУ́ХНУТИ, '
                                                             'не; мин. ч.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'НабУхати, -хаю, -єш, гл. 1) Наколотить. Набухали '
                                               'кулаччям по спині. 2) Налить или наложить слишком '
                                               'много.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}},
              {'headword': 'набуха́ти',
               'short_label': "збільшуватися в об'ємі, набрякати від вологи (недок.)",
               'gloss': 'swell up, become engorged or bloated with moisture/sap (imperfective)',
               'pos': 'verb',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐbuˈxɑtɪ]'},
               'stress': {'form': 'набуха́ти',
                          'source': 'ВТС / СУМ-11',
                          'url': 'https://slovnyk.me/dict/vts/набухати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': "Означає «збільшуватися в об'ємі, розпухати від вологи чи соків "
                                   '(недок. до набухнути)». Не плутати з «набу́хати» (накидати або '
                                   'налити багато чогось).',
               'meaning': {'definitions': ["Збільшуватися в об'ємі, набрякати, розпухати від "
                                           'вологи, рідини або соків.'],
                           'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАБУХА́ТИ, а́є, недок., НАБУ́ХНУТИ, '
                                                             'не; мин. ч. набу́х, ла, ло; док. 1. '
                                                             'Збільшуватися в об’ємі, розпухати '
                                                             '(від припливу крові, молока і т. '
                                                             'ін.).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'}}],
 'наварний': [{'headword': 'нава́рний',
               'short_label': 'густий і поживний, із густим наваром (про страву)',
               'gloss': 'rich, broth-heavy, thick and substantial (of soup or stew)',
               'pos': 'adj',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐˈwɑrnɪj]'},
               'stress': {'form': 'нава́рний',
                          'source': 'ВТС / СУМ-11',
                          'url': 'https://slovnyk.me/dict/vts/наварний'},
               'morphology': {'pos': 'прикметник',
                              'paradigm': {'kind': 'adjective',
                                           'forms': {'masculine': 'нава́рний',
                                                     'feminine': 'нава́рна',
                                                     'neuter': 'нава́рне',
                                                     'plural': 'нава́рні'}}},
               'distinction_note': 'Означає «наваристий, жирний, з густим поживним наваром (про '
                                   'бульйон, борщ)». Не плутати з технічним «наварни́й» '
                                   '(виготовлений наварюванням сталі).',
               'meaning': {'definitions': ['Те саме, що нава́ристий: густий, багатий наваром.'],
                           'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАВА́РНИЙ, а, е. Те саме, що '
                                                             'нава́ристий. НАВАРНИ́Й, а, е, техн.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'}},
              {'headword': 'наварни́й',
               'short_label': 'виготовлений або зміцнений зварюванням (техн.)',
               'gloss': 'welded-on, hard-faced, surfaced by welding (technical)',
               'pos': 'adj',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐwɐrˈnɪj]'},
               'stress': {'form': 'наварни́й',
                          'source': 'ВТС / СУМ-11',
                          'url': 'https://slovnyk.me/dict/vts/наварний'},
               'morphology': {'pos': 'прикметник',
                              'paradigm': {'kind': 'adjective',
                                           'forms': {'masculine': 'наварни́й',
                                                     'feminine': 'наварна́',
                                                     'neuter': 'наварне́',
                                                     'plural': 'наварні́'}}},
               'distinction_note': 'Означає «прироблений за допомогою зварювального наплавлення '
                                   'металу (техн.)». Не плутати з кулінарним «нава́рний» '
                                   '(наваристий).',
               'meaning': {'definitions': ['Прироблений або зміцнений за допомогою зварювального '
                                           'наплавлення (техн.).'],
                           'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАВАРНИ́Й, а, е, техн. Прироблений '
                                                             'за допомогою наварювання.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'}}],
 'навозити': [{'headword': 'наво́зити',
               'short_label': 'доставляти або звозити транспортом у великій кількості (недок.)',
               'gloss': 'cart, transport or haul in large quantities (imperfective)',
               'pos': 'verb',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐˈwɔzɪtɪ]'},
               'stress': {'form': 'наво́зити',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/навозити'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': 'Означає «доставляти або звозити транспортом у великій '
                                   'кількості (недок. до навезти)». Не плутати з доконаним '
                                   '«навози́ти» (за кілька рейсів доставити багато чогось або '
                                   'угноювати ниву).',
               'meaning': {'definitions': ['Привозити кого-, що-небудь у великій кількості '
                                           '(недоконаний вид).'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАВО́ЗИТИ, о́жу, о́зиш, недок., '
                                                             'НАВЕЗТИ,́ зу́, зе́ш; мин. ч. наві́з, '
                                                             'навезла́, ло́; док., перех. '
                                                             'Привозити кого-, що-небудь у великій '
                                                             'кількості.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'НавОзити, -жу, -зиш, сов. в. навезтИ, -зУ, -зЕш, '
                                               'гл. Навозить, навезть. Дідова дівка навезла усякої '
                                               'всячини. Рудч. Ск. II. 58.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}},
              {'headword': 'навози́ти',
               'short_label': 'доставити за кілька рейсів (док.) або удобрити гноєм',
               'gloss': 'haul in multiple cartloads (perf.) or fertilize with manure',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐwɔˈzɪtɪ]'},
               'stress': {'form': 'навози́ти',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/навозити'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «за кілька заходів привезти що-небудь у великій '
                                   'кількості (док.) або удобрити поле гноєм». Не плутати з '
                                   'недоконаним «наво́зити».',
               'meaning': {'definitions': ['За кілька заходів привезти що-небудь у великій '
                                           'кількості (доконаний вид); удобрити гноєм.'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАВОЗИ́ТИ, о́жу, о́зиш, док., перех. '
                                                             'За кілька заходів привезти що-небудь '
                                                             'у великій кількості. — Якого хліба '
                                                             'навозив!.. — подумав він із '
                                                             'заздрістю, мало не з ненавистю до '
                                                             'брата (Коцюб., І, 1955, 120); Бразд '
                                                             'подивився навкруг, погладив свою '
                                                             'бороду.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'НавозИти 2, -жУ, -зиш, гл. = понавозити. Зо всього '
                                               'світу навозили у замок найдорожчих напитків. Стор. '
                                               'МПр. 67.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}}],
 'назубок': [{'headword': 'назу́бок',
              'short_label': 'столярний напилок для насікання зубців (спец.)',
              'gloss': 'special file used for cutting saw teeth or serrations (specialized tool)',
              'pos': 'noun',
              'cefr': 'C1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[nɐˈzubɔk]'},
              'stress': {'form': 'назу́бок',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/назубок'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'назу́бок',
                                                                 'plural': 'назу́бки'},
                                                    'родовий': {'singular': 'назу́бка',
                                                                'plural': 'назу́бків'},
                                                    'давальний': {'singular': 'назу́бку',
                                                                  'plural': 'назу́бкам'},
                                                    'знахідний': {'singular': 'назу́бок',
                                                                  'plural': 'назу́бки'},
                                                    'орудний': {'singular': 'назу́бком',
                                                                'plural': 'назу́бками'},
                                                    'місцевий': {'singular': 'назу́бку',
                                                                 'plural': 'назу́бках'},
                                                    'кличний': {'singular': 'назу́бку',
                                                                'plural': 'назу́бки'}}}},
              'distinction_note': 'Означає «інструмент, напилок для випилювання зубців або насічок '
                                  "(іменник)». Не плутати з прислівником «назубо́к» (напам'ять, "
                                  'досконало).',
              'meaning': {'definitions': ['Напилок, яким випилюють зубці, роблять насічку, '
                                          'зазублини тощо.'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'НАЗУ́БОК, бка, ч. Напилок, яким '
                                                            'випилюють зубці, роблять насічку, '
                                                            'зазублини і т. ін. НАЗУБО́К, присл., '
                                                            'розм. Дуже добре, грунтовно. '
                                                            'Северко..',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}},
             {'headword': 'назубо́к',
              'short_label': "напам'ять, до найдрібніших деталей (розм., присл.)",
              'gloss': 'by heart, thoroughly, down to the smallest detail (colloquial adv.)',
              'pos': 'adv',
              'cefr': 'B1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[nɐzuˈbɔk]'},
              'stress': {'form': 'назубо́к',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/назубок'},
              'morphology': {'pos': 'прислівник', 'paradigm': {'kind': 'adverb'}},
              'distinction_note': "Означає «дуже добре, ґрунтовно, напам'ять (прислівник: знати "
                                  'назубок)». Не плутати з іменником «назу́бок» (напилок для '
                                  'зубців).',
              'meaning': {'definitions': ["Дуже добре, ґрунтовно, напам'ять (розм.)."],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'НАЗУБО́К, присл., розм. Дуже добре, '
                                                            'грунтовно. Северко..',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}}],
 'наслухати': [{'headword': 'наслу́хати',
                'short_label': 'дізнатися з чуток або переказів (розм., док.)',
                'gloss': 'hear of, learn through rumor or gossip, overhear (colloquial, perf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[nɐˈsluxɐtɪ]'},
                'stress': {'form': 'наслу́хати',
                           'source': 'Грінченко (1907) / ВТС',
                           'url': 'https://slovnyk.me/dict/vts/наслухати'},
                'morphology': {'pos': 'дієслово',
                               'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає «довідатися з розповідей, чуток про що-небудь; '
                                    'прочути (док.)». Не плутати з «наслуха́ти» (недоконаний вид: '
                                    'напружено прислухатися).',
                'meaning': {'definitions': ['Довідатися з розповідей або чуток про що-небудь; '
                                            'прочути (розм., док.).'],
                            'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'НАСЛУ́ХАТИ, аю, аєш, док., розм. 1. '
                                                              'Довідатися з розповідей, чуток про '
                                                              'що-небудь; прочути. 2. Багато '
                                                              'почути, довідатися. *Образно. '
                                                              'Повноводий Славуто! Немало наслухав '
                                                              'І немало зазнав на віку (Перв., І, '
                                                              '1958, 210).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної прозорості.'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'Наслухати, -хаю, -єш, гл. Услышать, прослышать. '
                                                'Наслухав я, що там добре живеться.',
                                       'historical_note': 'Автентичне народне мововживання, '
                                                          'зафіксоване Борисом Грінченком в умовах '
                                                          'дії антиукраїнських імперських указів '
                                                          '(Валуєвського циркуляра 1863 р. та '
                                                          'Емського указу 1876 р.).'}},
               {'headword': 'наслуха́ти',
                'short_label': 'напружено прислухатися, виловлювати звуки (недок.)',
                'gloss': "listen intently, strain one's ears to catch sounds, eavesdrop "
                         '(imperfective)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[nɐsluˈxɑtɪ]'},
                'stress': {'form': 'наслуха́ти',
                           'source': 'Грінченко (1907) / ВТС',
                           'url': 'https://slovnyk.me/dict/vts/наслухати'},
                'morphology': {'pos': 'дієслово',
                               'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': 'Означає «напружуючи слух, старатися почути що-небудь; '
                                    'прислухатися (недок.)». Не плутати з «наслу́хати» (доконаний '
                                    'вид: дізнатися з чуток).',
                'meaning': {'definitions': ['Напружуючи слух, старатися почути що-небудь; уважно '
                                            'прислухатися (недоконаний вид).'],
                            'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'НАСЛУХА́ТИ, а́ю, а́єш і рідко '
                                                              'НАСЛУ́ХУВАТИ, ую, уєш, недок. 1. '
                                                              'неперех. Напружуючи слух, старатися '
                                                              'почути що-небудь; прислухатися.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної прозорості.'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'Наслухати 2, -хАю, -єш, гл. Прислушиваться.',
                                       'historical_note': 'Автентичне народне мововживання, '
                                                          'зафіксоване Борисом Грінченком в умовах '
                                                          'дії антиукраїнських імперських указів '
                                                          '(Валуєвського циркуляра 1863 р. та '
                                                          'Емського указу 1876 р.).'}}],
 'настильний': [{'headword': 'насти́льний',
                 'short_label': 'пологої траєкторії, близький до землі (військ.)',
                 'gloss': 'flat-trajectory, grazing (of gunfire or projectile flight, military)',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[nɐˈstɪlʲnɪj]'},
                 'stress': {'form': 'насти́льний',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/настильний'},
                 'morphology': {'pos': 'прикметник',
                                'paradigm': {'kind': 'adjective',
                                             'forms': {'masculine': 'насти́льний',
                                                       'feminine': 'насти́льна',
                                                       'neuter': 'насти́льне',
                                                       'plural': 'насти́льні'}}},
                 'distinction_note': 'Означає «який рухається паралельно до поверхні землі на '
                                     'малій висоті (настильний вогонь, настильна траєкторія)». Не '
                                     "плутати з «настильни́й» (пов'язаний з настиланням "
                                     'підлоги/покрівлі).',
                 'meaning': {'definitions': ['Який рухається паралельно до поверхні землі на '
                                             'незначній висоті (про політ куль чи снарядів).'],
                             'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'НАСТИ́ЛЬНИЙ, а, е. Який рухається '
                                                               'паралельно до поверхні землі на '
                                                               'незначній висоті (про політ куль, '
                                                               'мін, снарядів і т. ін.). '
                                                               'Настильний вогонь. НАСТИЛЬНИ́Й, '
                                                               'а́, е́. Стос. до настилання.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної '
                                                                    'прозорості.'}},
                {'headword': 'настильни́й',
                 'short_label': 'призначений для настилання долівки або помосту',
                 'gloss': 'flooring, decking, relating to boarding or laying planks',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[nɐstɪlʲˈnɪj]'},
                 'stress': {'form': 'настильни́й',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/настильний'},
                 'morphology': {'pos': 'прикметник',
                                'paradigm': {'kind': 'adjective',
                                             'forms': {'masculine': 'настильни́й',
                                                       'feminine': 'настильна́',
                                                       'neuter': 'настильне́',
                                                       'plural': 'настильні́'}}},
                 'distinction_note': 'Означає «стосовний до настилання, настилу (настильні дошки, '
                                     'настильні роботи)». Не плутати з балістичним «насти́льний» '
                                     '(полога траєкторія).',
                 'meaning': {'definitions': ['Стосовний до настилання долівки, покрівлі, помосту.'],
                             'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'НАСТИЛЬНИ́Й, а́, е́. Стос. до '
                                                               'настилання. Настильні роботи.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної '
                                                                    'прозорості.'}}],
 'невигода': [{'headword': 'неви́года',
               'short_label': 'матеріальний збиток, втрата вигоди або прибутку',
               'gloss': 'material loss, disadvantage, lack of profit or benefit',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɛˈwɪɦɔdɐ]'},
               'stress': {'form': 'неви́года',
                          'source': 'ВТС / СУМ-11',
                          'url': 'https://slovnyk.me/dict/vts/невигода'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'неви́года',
                                                                  'plural': 'неви́годи'},
                                                     'родовий': {'singular': 'неви́годи',
                                                                 'plural': 'неви́год'},
                                                     'давальний': {'singular': 'неви́годі',
                                                                   'plural': 'неви́годам'},
                                                     'знахідний': {'singular': 'неви́году',
                                                                   'plural': 'неви́годи'},
                                                     'орудний': {'singular': 'неви́годою',
                                                                 'plural': 'неви́годами'},
                                                     'місцевий': {'singular': 'неви́годі',
                                                                  'plural': 'неви́годах'},
                                                     'кличний': {'singular': 'неви́годо',
                                                                 'plural': 'неви́годи'}}}},
               'distinction_note': 'Означає «матеріальний збиток, неотримання очікуваного прибутку '
                                   'чи користі». Не плутати з «невиго́да» (побутова незручність, '
                                   'дискомфорт).',
               'meaning': {'definitions': ['Матеріальні збитки, втрата вигоди.'],
                           'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НЕВИ́ГОДА, и, ж. Матеріальні збитки. '
                                                             'Молодий поміщик до копієчки '
                                                             'обчислив, яка йому невигода тримати '
                                                             'селян у лісах (Стельмах, Хліб.., '
                                                             '1959, 241). НЕВИГО́ДА, и, ж. Те '
                                                             'саме, що незру́чність. Від '
                                                             'Радивилова до Ковеля.. їхати вже '
                                                             'недовго, ..',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'}},
              {'headword': 'невиго́да',
               'short_label': 'побутова незручність, дискомфорт або труднощі',
               'gloss': 'inconvenience, discomfort, lack of comfort or household amenities',
               'pos': 'noun',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɛwɪˈɦɔdɐ]'},
               'stress': {'form': 'невиго́да',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/невигода'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'невиго́да',
                                                                  'plural': 'невиго́ди'},
                                                     'родовий': {'singular': 'невиго́ди',
                                                                 'plural': 'невиго́д'},
                                                     'давальний': {'singular': 'невиго́ді',
                                                                   'plural': 'невиго́дам'},
                                                     'знахідний': {'singular': 'невиго́ду',
                                                                   'plural': 'невиго́ди'},
                                                     'орудний': {'singular': 'невиго́дою',
                                                                 'plural': 'невиго́дами'},
                                                     'місцевий': {'singular': 'невиго́ді',
                                                                  'plural': 'невиго́дах'},
                                                     'кличний': {'singular': 'невиго́до',
                                                                 'plural': 'невиго́ди'}}}},
               'distinction_note': 'Означає «незручність, брак зручностей чи комфорту в житті чи '
                                   'дорозі». Не плутати з «неви́года» (матеріальний фінансовий '
                                   'збиток).',
               'meaning': {'definitions': ['Те саме, що незру́чність: брак зручностей, '
                                           'дискомфорт.'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НЕВИГО́ДА, и, ж. Те саме, що '
                                                             'незру́чність. Від Радивилова до '
                                                             'Ковеля.. їхати вже недовго, .. '
                                                             'тільки одна невигода — пересадка в '
                                                             'Здолбунові (Л.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Невигода, -ди, ж. Неудобство. Не так шкода, як '
                                               'невигода. Ном. № 2300.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}}],
 'неперехідний': [{'headword': 'неперехі́дний',
                   'short_label': 'непрохідний, якого не можна перетнути чи перейти',
                   'gloss': 'impassable, uncrossable, impenetrable (e.g. swamp or mountain range)',
                   'pos': 'adj',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[nɛpɛrɛˈxidnɪj]'},
                   'stress': {'form': 'неперехі́дний',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/неперехідний'},
                   'morphology': {'pos': 'прикметник',
                                  'paradigm': {'kind': 'adjective',
                                               'forms': {'masculine': 'неперехі́дний',
                                                         'feminine': 'неперехі́дна',
                                                         'neuter': 'неперехі́дне',
                                                         'plural': 'неперехі́дні'}}},
                   'distinction_note': 'Означає «якого важко або неможливо перейти; непрохідний '
                                       '(гори, болота)». Не плутати з «неперехідни́й» (граматичний '
                                       'термін: дієслово без прямого додатка; або вічний, '
                                       'неминущий).',
                   'meaning': {'definitions': ['Якого важко, неможливо перейти (про гори, ліси, '
                                               'ріки тощо).'],
                               'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НЕПЕРЕХІ́ДНИЙ, а, е. Якого '
                                                                 'важко, неможливо перейти. — '
                                                                 'Військо зараз стоїть біля '
                                                                 'Ісакчі. Позаду нього Волконські '
                                                                 'гори, майже неперехідні навіть '
                                                                 'улітку (Тулуб, Людолови, II, '
                                                                 '1957, 500). НЕПЕРЕХІДНИ́Й, а́, '
                                                                 'е́, грам.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський '
                                                                      'період (СУМ-11). Наведено '
                                                                      'для лексикографічної '
                                                                      'прозорості.'}},
                  {'headword': 'неперехідни́й',
                   'short_label': 'граматично неперехідний (без додатка) або вічний',
                   'gloss': 'intransitive (grammatical term) or enduring, lasting, imperishable',
                   'pos': 'adj',
                   'cefr': 'B1',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[nɛpɛrɛxidˈnɪj]'},
                   'stress': {'form': 'неперехідни́й',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/неперехідний'},
                   'morphology': {'pos': 'прикметник',
                                  'paradigm': {'kind': 'adjective',
                                               'forms': {'masculine': 'неперехідни́й',
                                                         'feminine': 'неперехідна́',
                                                         'neuter': 'неперехідне́',
                                                         'plural': 'неперехідні́'}}},
                   'distinction_note': 'Означає «грам. дієслово, дія якого не переходить на прямий '
                                       'додаток» або переносно «вічний, неминущий». Не плутати з '
                                       'географічним «неперехі́дний» (непрохідний).',
                   'meaning': {'definitions': ["Який позначає дію, що не переходить на об'єкт "
                                               '(грам.); вічний, постійний.'],
                               'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НЕПЕРЕХІДНИ́Й, а́, е́, грам. '
                                                                 'Який позначає дію, що не '
                                                                 'переходить на об’єкт (про '
                                                                 'дієслово). До неперехідних '
                                                                 'належать дієслова, що означають '
                                                                 'рух і положення в просторі.., '
                                                                 'фізичний і духовний стан (Сл. '
                                                                 'лінгв.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський '
                                                                      'період (СУМ-11). Наведено '
                                                                      'для лексикографічної '
                                                                      'прозорості.'}}],
 'неповоротний': [{'headword': 'неповоро́тний',
                   'short_label': 'незворотний, якого не можна повернути назад',
                   'gloss': 'irreversible, irrevocable, that will never return (e.g. loss or time)',
                   'pos': 'adj',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[nɛpɔwɔˈrɔtnɪj]'},
                   'stress': {'form': 'неповоро́тний',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/неповоротний'},
                   'morphology': {'pos': 'прикметник',
                                  'paradigm': {'kind': 'adjective',
                                               'forms': {'masculine': 'неповоро́тний',
                                                         'feminine': 'неповоро́тна',
                                                         'neuter': 'неповоро́тне',
                                                         'plural': 'неповоро́тні'}}},
                   'distinction_note': 'Означає «який не повернеться назад, не повториться; '
                                       'незворотний, безповоротний (неповоротна втрата)». Не '
                                       'плутати з «неповоротни́й» (вайлуватий, неповороткий).',
                   'meaning': {'definitions': ['Який не повернеться, не повториться; незворотний.'],
                               'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НЕПОВОРО́ТНИЙ, а, е. Який не '
                                                                 'повернеться, не повториться.',
                                                   'sovietization_risk': 1,
                                                   'keywords': ['переможний Жовтень',
                                                                'земельна власність'],
                                                   'historical_note': 'Зафіксовано в радянський '
                                                                      'період (СУМ-11) з '
                                                                      'характерною радянською '
                                                                      'ідеологічною ілюстрацією '
                                                                      '(«переможний Жовтень»). '
                                                                      'Наведено для '
                                                                      'лексикографічної '
                                                                      'прозорості.'}},
                  {'headword': 'неповоротни́й',
                   'short_label': 'вайлуватий, повільний у рухах (неповороткий)',
                   'gloss': 'clumsy, unwieldy, sluggish, slow-moving (person or animal)',
                   'pos': 'adj',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[nɛpɔwɔrɔtˈnɪj]'},
                   'stress': {'form': 'неповоротни́й',
                              'source': 'Грінченко (1907) / ВТС',
                              'url': 'https://slovnyk.me/dict/vts/неповоротний'},
                   'morphology': {'pos': 'прикметник',
                                  'paradigm': {'kind': 'adjective',
                                               'forms': {'masculine': 'неповоротни́й',
                                                         'feminine': 'неповоротна́',
                                                         'neuter': 'неповоротне́',
                                                         'plural': 'неповоротні́'}}},
                   'distinction_note': 'Означає «неповороткий, вайлуватий, повільний або '
                                       'незграбний у рухах чи діях». Не плутати з «неповоро́тний» '
                                       '(незворотний).',
                   'meaning': {'definitions': ['Те саме, що неповоротки́й: вайлуватий, повільний, '
                                               'незграбний.'],
                               'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НЕПОВОРОТНИ́Й, а́, е́. Те саме, '
                                                                 'що неповоротки́й. Матня '
                                                                 'одрізнявся од усього '
                                                                 'товариства..',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський '
                                                                      'період (СУМ-11). Наведено '
                                                                      'для лексикографічної '
                                                                      'прозорості.'},
                   'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                          'quote': 'Неповоротний, -А, -Е Неповоротливый. Н. Вол. '
                                                   'у. Левиц. Пов. 10.',
                                          'historical_note': 'Автентичне народне мововживання, '
                                                             'зафіксоване Борисом Грінченком в '
                                                             'умовах дії антиукраїнських '
                                                             'імперських указів (Валуєвського '
                                                             'циркуляра 1863 р. та Емського указу '
                                                             '1876 р.).'}}],
 'оббігати': [{'headword': 'оббі́гати',
               'short_label': 'побувати скрізь бігом, відвідати багато місць (док.)',
               'gloss': 'run around to multiple places, visit everywhere in a hurry (perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ɔbˈbiɦɐtɪ]'},
               'stress': {'form': 'оббі́гати',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/оббігати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «бігаючи, побувати по черзі в багатьох місцях або '
                                   'відвідати багатьох осіб (док.)». Не плутати з «оббіга́ти» '
                                   '(недоконаний вид: бігти по колу або обминати перешкоду).',
               'meaning': {'definitions': ['Бігаючи, побувати по черзі в багатьох місцях, '
                                           'відвідати багатьох осіб (доконаний вид).'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ОББІ́ГАТИ, аю, аєш, док., перех. і '
                                                             'неперех. Бігаючи, побувати по черзі '
                                                             'в багатьох місцях, відвідати '
                                                             'багатьох осіб і т. ін.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Оббігати 2, -гаю, -єш, гл. Оббегать. Усіх подруг '
                                               'сьогодні оббігала, — заполочі хотіла позичити. '
                                               'Харьк.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}},
              {'headword': 'оббіга́ти',
               'short_label': 'бігти по колу навколо чогось або оминати (недок.)',
               'gloss': 'run around in a circle, bypass or skirt obstacles while running '
                        '(imperfective)',
               'pos': 'verb',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ɔbbiˈɦɑtɪ]'},
               'stress': {'form': 'оббіга́ти',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/оббігати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': 'Означає «біжучи навкруги чого-небудь, описувати коло або '
                                   'оминати перешкоду (недок. до оббігти)». Не плутати з доконаним '
                                   '«оббі́гати».',
               'meaning': {'definitions': ['Біжучи навкруги чого-небудь, описувати замкнуте коло; '
                                           'оминати перешкоду бігом.'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ОББІГА́ТИ, а́ю, а́єш, недок., '
                                                             'ОББІ́ГТИ, оббіжу́, оббіжи́ш, док. 1. '
                                                             'перех. і неперех. Біжучи навкруги '
                                                             'чого-небудь, описувати замкнуте '
                                                             'коло.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Оббігати, -гАю, -єш, сов. в. оббігти, -біжу, -жИш, '
                                               'гл. 1) Обегать, обежать.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}}],
 'обводити': [{'headword': 'обво́дити',
               'short_label': 'окреслювати контуром або водити когось навколо (недок.)',
               'gloss': 'trace an outline, draw a perimeter around or lead around (imperfective)',
               'pos': 'verb',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ɔbˈwɔdɪtɪ]'},
               'stress': {'form': 'обво́дити',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/обводити'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': 'Означає «ведучи кого-небудь, обходити навколо чогось; або '
                                   'проводити лінію довкола (недок. до обвести)». Не плутати з '
                                   'доконаним «обводи́ти» (водячи, побувати скрізь).',
               'meaning': {'definitions': ['Ведучи кого-небудь, обходити з ним навколо чогось; '
                                           'креслити лінію довкола.'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ОБВО́ДИТИ, джу, диш, недок., '
                                                             'ОБВЕСТИ́, веду́, веде́ш, док. 1. '
                                                             'перех. Ведучи кого-небудь, обходити '
                                                             'з ним навколо чогось.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Обводити, -джу, -диш, сов. в. обвести, -ведУ, '
                                               '-дЕш, гл. Обводить, обвести. Обвів його круг хати.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}},
              {'headword': 'обводи́ти',
               'short_label': 'водячи когось, відвідати багато місць (док.)',
               'gloss': 'take someone around to many places, lead around everywhere (perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ɔbwɔˈdɪtɪ]'},
               'stress': {'form': 'обводи́ти',
                          'source': 'ВТС / СУМ-11',
                          'url': 'https://slovnyk.me/dict/vts/обводити'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «водячи кого-небудь, побувати з ним у багатьох місцях '
                                   '(доконаний вид)». Не плутати з недоконаним «обво́дити».',
               'meaning': {'definitions': ['Водячи кого-небудь, побувати з ним у багатьох місцях '
                                           '(доконаний вид).'],
                           'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ОБВОДИ́ТИ, воджу́, во́диш, док., '
                                                             'перех. Водячи кого-небудь, побувати '
                                                             'з ним у багатьох місцях.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'}}],
 'обідець': [{'headword': 'обі́дець',
              'short_label': 'ободок, невелика дужка або обруч колеса',
              'gloss': 'small rim, hoop, bezel or circlet (diminutive of обід - rim/hoop)',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ɔˈbidɛt͡sʲ]'},
              'stress': {'form': 'обі́дець',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/обідець'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'обі́дець',
                                                                 'plural': 'обі́дці'},
                                                    'родовий': {'singular': 'обі́дця',
                                                                'plural': 'обі́дців'},
                                                    'давальний': {'singular': 'обі́дцю',
                                                                  'plural': 'обі́дцям'},
                                                    'знахідний': {'singular': 'обі́дець',
                                                                  'plural': 'обі́дці'},
                                                    'орудний': {'singular': 'обі́дцем',
                                                                'plural': 'обі́дцями'},
                                                    'місцевий': {'singular': 'обі́дці',
                                                                 'plural': 'обі́дцях'},
                                                    'кличний': {'singular': 'обі́дцю',
                                                                'plural': 'обі́дці'}}}},
              'distinction_note': 'Означає «зменшене до обід (дужка, ободок колеса, обруч)». Не '
                                  'плутати з «обіде́ць» (пестливе до обід — денна трапеза, прийом '
                                  'їжі).',
              'meaning': {'definitions': ['Зменшене до обід (обруч, ободок, дужка колеса чи '
                                          'решета).'],
                          'source': 'Грінченко (1907) / ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ОБІ́ДЕЦЬ, дця́, ч. Зменш. до обі́д 2. '
                                                            'Батькові очі круглі, з червоними '
                                                            'обідцями від безсоння (Донч., Вибр., '
                                                            '1948, 62).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Обідець 2, -дця, м. 1) Ум. от обід. Ободок. 2) '
                                              'Кольцо, колечко.',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}},
             {'headword': 'обіде́ць',
              'short_label': 'пестлива назва обідньої трапези (невеликий обід)',
              'gloss': 'nice midday meal, small dinner (affectionate diminutive of обід - meal)',
              'pos': 'noun',
              'cefr': 'B1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ɔbiˈdɛt͡sʲ]'},
              'stress': {'form': 'обіде́ць',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/обідець'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'обіде́ць',
                                                                 'plural': 'обідці́'},
                                                    'родовий': {'singular': 'обі́дця',
                                                                'plural': 'обідці́в'},
                                                    'давальний': {'singular': 'обі́дцю',
                                                                  'plural': 'обідця́м'},
                                                    'знахідний': {'singular': 'обіде́ць',
                                                                  'plural': 'обідці́'},
                                                    'орудний': {'singular': 'обі́дцем',
                                                                'plural': 'обідця́ми'},
                                                    'місцевий': {'singular': 'обі́дці',
                                                                 'plural': 'обідця́х'},
                                                    'кличний': {'singular': 'обі́дцю',
                                                                'plural': 'обідці́'}}}},
              'distinction_note': 'Означає «зменшено-пестливе до обід (денна трапеза, обід)». Не '
                                  'плутати з «обі́дець» (ободок, дужка колеса).',
              'meaning': {'definitions': ['Зменшено-пестливе до обід (трапеза, полуденок).'],
                          'source': 'Грінченко (1907) / ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ОБІДЕ́ЦЬ, дця, ч. Зменш.-пестл. до '
                                                            'обі́д 1, 2.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Обідець 1, -дця, м. Ум. от обід.',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}}],
 'обрізання': [{'headword': 'обрі́зання',
                'short_label': 'сакральний релігійний обряд циркумцизії',
                'gloss': 'circumcision (religious ritual rite)',
                'pos': 'noun',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[ɔˈbrizɐnʲːɐ]'},
                'stress': {'form': 'обрі́зання',
                           'source': 'ВТС / СУМ-11',
                           'url': 'https://slovnyk.me/dict/vts/обрізання'},
                'morphology': {'pos': 'іменник',
                               'paradigm': {'kind': 'noun',
                                            'gender': 'середній',
                                            'animacy': 'inanimate',
                                            'cases': {'називний': {'singular': 'обрі́зання',
                                                                   'plural': 'обрі́зання'},
                                                      'родовий': {'singular': 'обрі́зання',
                                                                  'plural': 'обрі́зань'},
                                                      'давальний': {'singular': 'обрі́занню',
                                                                    'plural': 'обрі́занням'},
                                                      'знахідний': {'singular': 'обрі́зання',
                                                                    'plural': 'обрі́зання'},
                                                      'орудний': {'singular': 'обрі́занням',
                                                                  'plural': 'обрі́заннями'},
                                                      'місцевий': {'singular': 'обрі́занні',
                                                                   'plural': 'обрі́заннях'},
                                                      'кличний': {'singular': 'обрі́зання',
                                                                  'plural': 'обрі́зання'}}}},
                'distinction_note': 'Означає «релігійний обряд циркумцизії у юдеїв, мусульман '
                                    'тощо». Не плутати з «обріза́ння» (дія за значенням «обрізати» '
                                    '— підрізування гілок дерев або паперу).',
                'meaning': {'definitions': ['Релігійний обряд відсікання крайньої плоті.'],
                            'source': 'ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ОБРІ́ЗАННЯ, я, с. Релігійний обряд '
                                                              'у євреїв та деяких інших народів, '
                                                              'який полягає у відрізанні крайньої '
                                                              'плоті чоловічого члена. ОБРІЗА́ННЯ, '
                                                              'я, с. Дія за знач. обріза́ти. На '
                                                              'заняттях гуртка юних садоводів Яків '
                                                              'Романович уже розповідав нам, для '
                                                              'чого потрібне..',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної прозорості.'}},
               {'headword': 'обріза́ння',
                'short_label': 'підрізування гілок дерев, країв паперу чи матеріалів',
                'gloss': 'pruning, trimming, cutting down or cropping (branches, paper, etc.)',
                'pos': 'noun',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[ɔbriˈzɑnʲːɐ]'},
                'stress': {'form': 'обріза́ння',
                           'source': 'ВТС / СУМ-11',
                           'url': 'https://slovnyk.me/dict/vts/обрізання'},
                'morphology': {'pos': 'іменник',
                               'paradigm': {'kind': 'noun',
                                            'gender': 'середній',
                                            'animacy': 'inanimate',
                                            'cases': {'називний': {'singular': 'обріза́ння',
                                                                   'plural': 'обріза́ння'},
                                                      'родовий': {'singular': 'обріза́ння',
                                                                  'plural': 'обріза́нь'},
                                                      'давальний': {'singular': 'обріза́нню',
                                                                    'plural': 'обріза́нням'},
                                                      'знахідний': {'singular': 'обріза́ння',
                                                                    'plural': 'обріза́ння'},
                                                      'орудний': {'singular': 'обріза́нням',
                                                                  'plural': 'обріза́ннями'},
                                                      'місцевий': {'singular': 'обріза́нні',
                                                                   'plural': 'обріза́ннях'},
                                                      'кличний': {'singular': 'обріза́ння',
                                                                  'plural': 'обріза́ння'}}}},
                'distinction_note': 'Означає «дія за значенням обрізати (вкорочення гілок дерев у '
                                    'садівництві, обрізка книг/паперу)». Не плутати з релігійним '
                                    'терміном «обрі́зання».',
                'meaning': {'definitions': ['Дія за значенням обріза́ти: підрізування гілок, '
                                            'обрізання країв тощо.'],
                            'source': 'ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ОБРІЗА́ННЯ, я, с. Дія за знач. '
                                                              'обріза́ти. На заняттях гуртка юних '
                                                              'садоводів Яків Романович уже '
                                                              'розповідав нам, для чого потрібне..',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної '
                                                                   'прозорості.'}}],
 'окісний': [{'headword': 'о́кісний',
              'short_label': "пов'язаний зі свинячим або м'ясним окостом (кулін.)",
              'gloss': 'pertaining to gammon, ham or rump meat cut (culinary)',
              'pos': 'adj',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈɔkisnɪj]'},
              'stress': {'form': 'о́кісний',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/окісний'},
              'morphology': {'pos': 'прикметник',
                             'paradigm': {'kind': 'adjective',
                                          'forms': {'masculine': 'о́кісний',
                                                    'feminine': 'о́кісна',
                                                    'neuter': 'о́кісне',
                                                    'plural': 'о́кісні'}}},
              'distinction_note': 'Означає «прикметник до о́кіст (стегнова частина туші, шинка)». '
                                  'Не плутати з анатомічним «окі́сний» (прикметник до окі́стя).',
              'meaning': {'definitions': ["Прикметник до о́кіст: пов'язаний із м'ясним окостом."],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'О́КІСНИЙ, а, е. Прикм. до о́кіст. '
                                                            'ОКІ́СНИЙ, а, е. Прикм.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}},
             {'headword': 'окі́сний',
              'short_label': "анатомічно пов'язаний з окістям кістки (анат.)",
              'gloss': 'periosteal, relating to the periosteum covering bones (anatomy)',
              'pos': 'adj',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ɔˈkisnɪj]'},
              'stress': {'form': 'окі́сний',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/окісний'},
              'morphology': {'pos': 'прикметник',
                             'paradigm': {'kind': 'adjective',
                                          'forms': {'masculine': 'окі́сний',
                                                    'feminine': 'окі́сна',
                                                    'neuter': 'окі́сне',
                                                    'plural': 'окі́сні'}}},
              'distinction_note': 'Означає «прикметник до окі́стя (оболонка кістки, periosteum)». '
                                  'Не плутати з кулінарним «о́кісний» (до о́кіст).',
              'meaning': {'definitions': ['Прикметник до окі́стя (сполучнотканинна оболонка '
                                          'кістки).'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ОКІ́СНИЙ, а, е. Прикм. до окі́стя.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}}],
 'окружний': [{'headword': 'окру́жний',
               'short_label': 'обхідний, кружний, не прямий (про дорогу, шлях)',
               'gloss': 'circuitous, roundabout, detour, peripheral (of a route or road)',
               'pos': 'adj',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ɔˈkruʒnɪj]'},
               'stress': {'form': 'окру́жний',
                          'source': 'ВТС / СУМ-11',
                          'url': 'https://slovnyk.me/dict/vts/окружний'},
               'morphology': {'pos': 'прикметник',
                              'paradigm': {'kind': 'adjective',
                                           'forms': {'masculine': 'окру́жний',
                                                     'feminine': 'окру́жна',
                                                     'neuter': 'окру́жне',
                                                     'plural': 'окру́жні'}}},
               'distinction_note': 'Означає «обхідний, не прямий, кружний (окружна дорога, '
                                   'окружний шлях)». Не плутати з «окружни́й» (територіальний, '
                                   'повітовий — прикметник до о́круг).',
               'meaning': {'definitions': ['Прикметник до округа: навколишній; обхідний, кружний '
                                           '(про шлях).'],
                           'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ОКРУ́ЖНИЙ, а, е. 1. Прикм. до '
                                                             'окру́га 1. — І Римськії поставить '
                                                             '[Еней] стіни, В них буде жити, як в '
                                                             'раю; Великі зробить переміни Во всім '
                                                             'окружнім там краю (Котл.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'}},
              {'headword': 'окружни́й',
               'short_label': "пов'язаний з територіальним округом (адмін., юрид.)",
               'gloss': 'district, regional, circuit (relating to an administrative district or '
                        'court)',
               'pos': 'adj',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ɔkruʒˈnɪj]'},
               'stress': {'form': 'окружни́й',
                          'source': 'ВТС / СУМ-11',
                          'url': 'https://slovnyk.me/dict/vts/окружний'},
               'morphology': {'pos': 'прикметник',
                              'paradigm': {'kind': 'adjective',
                                           'forms': {'masculine': 'окружни́й',
                                                     'feminine': 'окружна́',
                                                     'neuter': 'окружне́',
                                                     'plural': 'окружні́'}}},
               'distinction_note': 'Означає «прикметник до о́круг (окружний суд, окружне місто, '
                                   'окружна рада)». Не плутати з «окру́жний» (обхідний, кружний).',
               'meaning': {'definitions': ['Прикметник до о́круг: повітовий, районний, окружний '
                                           'суд.'],
                           'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ОКРУЖНИ́Й, а́, е́. 1. Прикм. до '
                                                             'о́круг. Приїхали [Славко і '
                                                             'Краньцовська ] в місто X. Це — '
                                                             'повітове місто, осідок староства й '
                                                             'окружного суду (Март., Тв., 1954, '
                                                             '258). Крайові, обласні.., окружні, '
                                                             'районні, міські, сільські..',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'}}],
 'описка': [{'headword': 'о́писка',
             'short_label': 'бура мінеральна глина для гончарної поливи та фарби',
             'gloss': 'brown iron-rich clay pigment used by potters (specialized craft term)',
             'pos': 'noun',
             'cefr': 'C1',
             'heritage_status': {'classification': 'standard',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[ˈɔpɪskɐ]'},
             'stress': {'form': 'о́писка',
                        'source': 'Грінченко (1907) / ВТС',
                        'url': 'https://slovnyk.me/dict/vts/описка'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'жіночий',
                                         'animacy': 'inanimate',
                                         'cases': {'називний': {'singular': 'о́писка',
                                                                'plural': 'о́писки'},
                                                   'родовий': {'singular': 'о́писки',
                                                               'plural': 'о́писок'},
                                                   'давальний': {'singular': 'о́писці',
                                                                 'plural': 'о́пискам'},
                                                   'знахідний': {'singular': 'о́писку',
                                                                 'plural': 'о́писки'},
                                                   'орудний': {'singular': 'о́пискою',
                                                               'plural': 'о́писками'},
                                                   'місцевий': {'singular': 'о́писці',
                                                                'plural': 'о́писках'},
                                                   'кличний': {'singular': 'о́писко',
                                                               'plural': 'о́писки'}}}},
             'distinction_note': 'Означає «бура залізиста глина, яку ремісники-гончарі '
                                 'застосовували як фарбу (спец.)». Не плутати з «опи́ска» (помилка '
                                 'в написаному тексті через неуважність).',
             'meaning': {'definitions': ['Бура від окисів заліза глина, яку гончарі '
                                         'використовували як фарбу (спец.).'],
                         'source': 'Грінченко (1907) / ВТС / СУМ-11'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'О́ПИСКА, и, ж., спец. Бура від окисів '
                                                           'заліза глина, яку ремісники-гончарі '
                                                           'використовували як фарбу. Місцеві '
                                                           'майстри користувалися невеликим числом '
                                                           'фарб: білою (побілка), жовтою (вохра), '
                                                           'цеглястою (червінь) та коричневою '
                                                           '(описка) (Нар. тв.',
                                             'sovietization_risk': 0,
                                             'keywords': [],
                                             'historical_note': 'Зафіксовано в радянський період '
                                                                '(СУМ-11). Наведено для '
                                                                'лексикографічної прозорості.'},
             'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                    'quote': 'Описка, -ки, ж. У горшечниковь: красильное вещество '
                                             '— болотная бобовая железная руда. Вас. 182.',
                                    'historical_note': 'Автентичне народне мововживання, '
                                                       'зафіксоване Борисом Грінченком в умовах '
                                                       'дії антиукраїнських імперських указів '
                                                       '(Валуєвського циркуляра 1863 р. та '
                                                       'Емського указу 1876 р.).'}},
            {'headword': 'опи́ска',
             'short_label': 'випадкова помилка в написаному тексті (lapsus calami)',
             'gloss': 'slip of the pen, clerical miswriting or typographical error in text',
             'pos': 'noun',
             'cefr': 'B1',
             'heritage_status': {'classification': 'standard',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[ɔˈpɪskɐ]'},
             'stress': {'form': 'опи́ска',
                        'source': 'ВТС / СУМ-11',
                        'url': 'https://slovnyk.me/dict/vts/описка'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'жіночий',
                                         'animacy': 'inanimate',
                                         'cases': {'називний': {'singular': 'опи́ска',
                                                                'plural': 'опи́ски'},
                                                   'родовий': {'singular': 'опи́ски',
                                                               'plural': 'опи́сок'},
                                                   'давальний': {'singular': 'опи́сці',
                                                                 'plural': 'опи́скам'},
                                                   'знахідний': {'singular': 'опи́ску',
                                                                 'plural': 'опи́ски'},
                                                   'орудний': {'singular': 'опи́скою',
                                                               'plural': 'опи́сками'},
                                                   'місцевий': {'singular': 'опи́сці',
                                                                'plural': 'опи́сках'},
                                                   'кличний': {'singular': 'опи́ско',
                                                               'plural': 'опи́ски'}}}},
             'distinction_note': 'Означає «помилка в написаному тексті переважно через неуважність '
                                 '(lapsus calami)». Не плутати з гончарним терміном «о́писка» '
                                 '(глина-фарба).',
             'meaning': {'definitions': ['Помилка в написаному тексті через неуважність '
                                         '(механічний огріх).'],
                         'source': 'ВТС / СУМ-11'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'ОПИ́СКА, и, ж. Помилка в написаному '
                                                           'тексті (перев. через неуважність).',
                                             'sovietization_risk': 0,
                                             'keywords': [],
                                             'historical_note': 'Зафіксовано в радянський період '
                                                                '(СУМ-11). Наведено для '
                                                                'лексикографічної прозорості.'}}],
 'пахолок': [{'headword': 'па́холок',
              'short_label': 'холка у тварини, коня (вет., діал.)',
              'gloss': 'withers of a horse or farm animal (veterinary, dialectal)',
              'pos': 'noun',
              'cefr': 'C1',
              'heritage_status': {'classification': 'authentic-dialectism',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈpɑxɔlɔk]'},
              'stress': {'form': 'па́холок',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/пахолок'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'па́холок',
                                                                 'plural': 'па́холки'},
                                                    'родовий': {'singular': 'па́холка',
                                                                'plural': 'па́холків'},
                                                    'давальний': {'singular': 'па́холку',
                                                                  'plural': 'па́холкам'},
                                                    'знахідний': {'singular': 'па́холок',
                                                                  'plural': 'па́холки'},
                                                    'орудний': {'singular': 'па́холком',
                                                                'plural': 'па́холками'},
                                                    'місцевий': {'singular': 'па́холку',
                                                                 'plural': 'па́холках'},
                                                    'кличний': {'singular': 'па́холку',
                                                                'plural': 'па́холки'}}}},
              'distinction_note': 'Означає «холка у коня (ділянка спини, діал./вет.)». Не плутати '
                                  'з «пахо́лок» (історичне: підліток, козацький джура, молодший '
                                  'слуга).',
              'meaning': {'definitions': ['Діалектна назва холки у тварини, коня.'],
                          'source': 'Грінченко (1907) / ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ПА́ХОЛОК, лка, ч., діал. Холка. '
                                                            'ПАХО́ЛОК, лка, ч., заст. 1. Слуга. '
                                                            '[Конон:] Я наче..',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Пахолок 2, -лка, м. Холка у лошади.',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}},
             {'headword': 'пахо́лок',
              'short_label': 'хлопчик, підліток, козацький джура чи слуга (іст.)',
              'gloss': 'boy, youth, page, squire or young servant lad (historical)',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[pɐˈxɔlɔk]'},
              'stress': {'form': 'пахо́лок',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/пахолок'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'animate',
                                          'cases': {'називний': {'singular': 'пахо́лок',
                                                                 'plural': 'пахо́лки'},
                                                    'родовий': {'singular': 'пахо́лка',
                                                                'plural': 'пахо́лків'},
                                                    'давальний': {'singular': 'пахо́лкові',
                                                                  'plural': 'пахо́лкам'},
                                                    'знахідний': {'singular': 'пахо́лка',
                                                                  'plural': 'пахо́лків'},
                                                    'орудний': {'singular': 'пахо́лком',
                                                                'plural': 'пахо́лками'},
                                                    'місцевий': {'singular': 'пахо́лкові',
                                                                 'plural': 'пахо́лках'},
                                                    'кличний': {'singular': 'пахо́лку',
                                                                'plural': 'пахо́лки'}}}},
              'distinction_note': 'Означає «хлопець-слуга, підліток, козацький зброєносець чи '
                                  'джура (іст.)». Не плутати з «па́холок» (холка у коня).',
              'meaning': {'definitions': ['Хлопець, підліток, молодший слуга при панові чи '
                                          'козацькому старшині (іст.).'],
                          'source': 'Грінченко (1907) / ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ПАХО́ЛОК, лка, ч., заст. 1. Слуга. '
                                                            '[Конон:] Я наче.. пахолок у моєї '
                                                            'жінки, що мушу робити тільки так, як '
                                                            'моїй жінці забагнеться (Кроп., II, '
                                                            '1958, 464); Пахолки у білих свитках '
                                                            'розносили мед у високих срібних '
                                                            'келихах (Рибак, Переясл. Рада, 1948, '
                                                            '278). 2.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Пахолок 1, -лка, м. 1) Мальчик, мальчуган; парень. '
                                              'Чуб. V. 917. Я малий пахолок, родився в вівторок, а '
                                              'в середу рано до школи оддано. Н. п. 2) Слуга.',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}}],
 'перевозити': [{'headword': 'перево́зити',
                 'short_label': 'транспортувати або переправляти транспортом (недок.)',
                 'gloss': 'transport, convey or ferry across somewhere (imperfective)',
                 'pos': 'verb',
                 'cefr': 'A2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛrɛˈwɔzɪtɪ]'},
                 'stress': {'form': 'перево́зити',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/перевозити'},
                 'morphology': {'pos': 'дієслово',
                                'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Означає «транспортувати, переправляти через що-небудь '
                                     'транспортом (недок. до перевезти)». Не плутати з доконаним '
                                     '«перевози́ти» (перевезти багатьох чи все за кілька рейсів).',
                 'meaning': {'definitions': ['Везучи, переправляти через що-небудь (воду, гори і '
                                             'т. ін.); транспортувати (недок.).'],
                             'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕВО́ЗИТИ, о́жу, о́зиш, недок., '
                                                               'ПЕРЕВЕЗТИ́, зу́, зе́ш; мин. ч. '
                                                               'переві́з, везла́, ло́; док., '
                                                               'перех. і без додатка. 1. Везучи, '
                                                               'переправляти через що-небудь, на '
                                                               'другий бік чогось. З тихим '
                                                               'плеском, таємничо Плине човник.. '
                                                               'Перевозять нас дівчата (Л.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Перевозити, -жу, -зиш, сов. в. перевезти, -зу, '
                                                 '-зЕш, гл. 1) Перевозить, перевезть.',
                                        'historical_note': 'Автентичне народне мововживання, '
                                                           'зафіксоване Борисом Грінченком в '
                                                           'умовах дії антиукраїнських імперських '
                                                           'указів (Валуєвського циркуляра 1863 р. '
                                                           'та Емського указу 1876 р.).'}},
                {'headword': 'перевози́ти',
                 'short_label': 'перевезти багатьох чи все за кілька заходів (док.)',
                 'gloss': 'transport all or many people/goods sequentially in multiple trips '
                          '(perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛrɛwɔˈzɪtɪ]'},
                 'stress': {'form': 'перевози́ти',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/перевозити'},
                 'morphology': {'pos': 'дієслово',
                                'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Означає «везучи, по черзі перемістити куди-небудь усіх або '
                                     'все майно (док. до поперевозити)». Не плутати з недоконаним '
                                     '«перево́зити».',
                 'meaning': {'definitions': ['Везучи, по черзі перемістити куди-небудь усіх чи '
                                             'багато чого-небудь (доконаний вид).'],
                             'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕВОЗИ́ТИ, ожу́, о́зиш, док., '
                                                               'перех. Везучи, по черзі '
                                                               'перемістити, переправити '
                                                               'куди-небудь усіх, багатьох або '
                                                               'все, багато чого-небудь.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної '
                                                                    'прозорості.'}}],
 'перекладка': [{'headword': 'пере́кладка',
                 'short_label': 'поперечина, опорний брус, перекладина або прокладка',
                 'gloss': 'crossbar, crossbeam, transverse strut or separating layer (noun)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛˈrɛklɐdkɐ]'},
                 'stress': {'form': 'пере́кладка',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/перекладка'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'жіночий',
                                             'animacy': 'inanimate',
                                             'cases': {'називний': {'singular': 'пере́кладка',
                                                                    'plural': 'пере́кладки'},
                                                       'родовий': {'singular': 'пере́кладки',
                                                                   'plural': 'пере́кладок'},
                                                       'давальний': {'singular': 'пере́кладці',
                                                                     'plural': 'пере́кладкам'},
                                                       'знахідний': {'singular': 'пере́кладку',
                                                                     'plural': 'пере́кладки'},
                                                       'орудний': {'singular': 'пере́кладкою',
                                                                   'plural': 'пере́кладками'},
                                                       'місцевий': {'singular': 'пере́кладці',
                                                                    'plural': 'пере́кладках'},
                                                       'кличний': {'singular': 'пере́кладко',
                                                                   'plural': 'пере́кладки'}}}},
                 'distinction_note': 'Означає «поперечна балка, планка, перекладина або розділова '
                                     'прокладка (іменник)». Не плутати з «перекла́дка» (дія за '
                                     'значенням «перекладати» — перекладання речей або переклад '
                                     'тексту).',
                 'meaning': {'definitions': ['Те саме, що перекла́дина: поперечний брус, планка, '
                                             'траверса.'],
                             'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕ́КЛАДКА, и, ж., рідко. Те '
                                                               'саме, що перекла́дина. До '
                                                               'баштового крана чіпляють '
                                                               'спеціальну поперечну перекладку — '
                                                               'траверсу (Наука.., 8, 1967, 3); '
                                                               'Василь.. опинився на турніку.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Перекладка, -ки, ж. Узенькая лента, которая '
                                                 'кладется на голову между двумя более широкими. '
                                                 'Подольск. у.',
                                        'historical_note': 'Автентичне народне мововживання, '
                                                           'зафіксоване Борисом Грінченком в '
                                                           'умовах дії антиукраїнських імперських '
                                                           'указів (Валуєвського циркуляра 1863 р. '
                                                           'та Емського указу 1876 р.).'}},
                {'headword': 'перекла́дка',
                 'short_label': 'процес перекладання речей або переклад тексту',
                 'gloss': 'process of repositioning, rearranging or translating text (verbal noun)',
                 'pos': 'noun',
                 'cefr': 'B1',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛrɛˈklɑdkɐ]'},
                 'stress': {'form': 'перекла́дка',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/перекладка'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'жіночий',
                                             'animacy': 'inanimate',
                                             'cases': {'називний': {'singular': 'перекла́дка',
                                                                    'plural': 'перекла́дки'},
                                                       'родовий': {'singular': 'перекла́дки',
                                                                   'plural': 'перекла́док'},
                                                       'давальний': {'singular': 'перекла́дці',
                                                                     'plural': 'перекла́дкам'},
                                                       'знахідний': {'singular': 'перекла́дку',
                                                                     'plural': 'перекла́дки'},
                                                       'орудний': {'singular': 'перекла́дкою',
                                                                   'plural': 'перекла́дками'},
                                                       'місцевий': {'singular': 'перекла́дці',
                                                                    'plural': 'перекла́дках'},
                                                       'кличний': {'singular': 'перекла́дко',
                                                                   'plural': 'перекла́дки'}}}},
                 'distinction_note': 'Означає «дія за значенням перекласти, перекладати '
                                     '(перекладання речей чи переклад тексту)». Не плутати з '
                                     'предметним іменником «пере́кладка» (перекладина).',
                 'meaning': {'definitions': ['Дія за значенням перекла́сти, переклада́ти '
                                             '(переміщення на інше місце або переклад тексту).'],
                             'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕКЛА́ДКА, и, ж., рідко. Дія за '
                                                               'знач. перекла́сти, переклада́ти 1.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної '
                                                                    'прозорості.'}}],
 'переливний': [{'headword': 'перели́вний',
                 'short_label': 'мінливий барвами або тонами, райдужний, переливчастий',
                 'gloss': 'iridescent, shimmering, playing with shades of light or sound',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛrɛˈlɪwnɪj]'},
                 'stress': {'form': 'перели́вний',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/переливний'},
                 'morphology': {'pos': 'прикметник',
                                'paradigm': {'kind': 'adjective',
                                             'forms': {'masculine': 'перели́вний',
                                                       'feminine': 'перели́вна',
                                                       'neuter': 'перели́вне',
                                                       'plural': 'перели́вні'}}},
                 'distinction_note': 'Означає «який грає переливами світла, барв або звуків; '
                                     'райдужний (переливні фарби неба)». Не плутати з '
                                     'гідротехнічним «переливни́й» (для переливання води).',
                 'meaning': {'definitions': ['Стосовний до переливу барв чи звуків; мінливий, '
                                             'райдужний.'],
                             'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕЛИ́ВНИЙ, а, е. Стос. до '
                                                               'перели́в 2, 3; з переливами. '
                                                               'Скільки раз я бачу, як зоря цвіте, '
                                                               'як на небі грають фарби переливні '
                                                               '(Сос., II, 1958, 56); Ой колись у '
                                                               'дні щасливі лилась пісня з серця '
                                                               'дна, як той щебет соловія — '
                                                               'переливна та бурна (У.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної '
                                                                    'прозорості.'}},
                {'headword': 'переливни́й',
                 'short_label': 'призначений для зливу або скидання рідини (гідрол., техн.)',
                 'gloss': 'overflow, spillway, overflow-type (relating to liquid overflow or '
                          'drainage)',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛrɛlʲiwˈnɪj]'},
                 'stress': {'form': 'переливни́й',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/переливний'},
                 'morphology': {'pos': 'прикметник',
                                'paradigm': {'kind': 'adjective',
                                             'forms': {'masculine': 'переливни́й',
                                                       'feminine': 'переливна́',
                                                       'neuter': 'переливне́',
                                                       'plural': 'переливні́'}}},
                 'distinction_note': "Означає «пов'язаний із переливанням рідини через край "
                                     '(переливні джерела, переливна гребля, переливний отвір)». Не '
                                     'плутати з естетичним «перели́вний» (райдужний).',
                 'meaning': {'definitions': ["Пов'язаний із переливанням рідини через перешкоду чи "
                                             'край резервуара (гідрол., техн.).'],
                             'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕЛИВНИ́Й, а́, е́. Пов’язаний з '
                                                               'переливанням рідини. Котловинні '
                                                               'джерела, або переливні. '
                                                               'Утворюються в умовах, коли '
                                                               'водотривкий шар залягає у вигляді '
                                                               'улоговини із угнутою серединою. '
                                                               'Вода..',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної '
                                                                    'прозорості.'}}],
 'переруб': [{'headword': 'пере́руб',
              'short_label': 'засік, закром для зерна в коморі чи стодолі (зах.)',
              'gloss': 'grain bin, storage compartment in a granary or barn (western dialectal)',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'authentic-dialectism',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[pɛˈrɛrub]'},
              'stress': {'form': 'пере́руб',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/переруб'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'пере́руб',
                                                                 'plural': 'пере́руби'},
                                                    'родовий': {'singular': 'пере́руба',
                                                                'plural': 'пере́рубів'},
                                                    'давальний': {'singular': 'пере́рубу',
                                                                  'plural': 'пере́рубам'},
                                                    'знахідний': {'singular': 'пере́руб',
                                                                  'plural': 'пере́руби'},
                                                    'орудний': {'singular': 'пере́рубом',
                                                                'plural': 'пере́рубами'},
                                                    'місцевий': {'singular': 'пере́рубі',
                                                                 'plural': 'пере́рубах'},
                                                    'кличний': {'singular': 'пере́рубе',
                                                                'plural': 'пере́руби'}}}},
              'distinction_note': 'Означає «засік у коморі або стодолі для зберігання зерна (зах., '
                                  'діалектне)». Не плутати з «переру́б» (лісове: вирубування лісу '
                                  'понад норму).',
              'meaning': {'definitions': ['Засік у стодолі чи коморі (зах.).'],
                          'source': 'Грінченко (1907) / ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ПЕРЕ́РУБ, а, ч., зах. Засік. Ночували '
                                                            'ми, як звичайно, в стодолі: мужчини в '
                                                            'однім перерубі на соломі (Фр., IV, '
                                                            '1950, 260). ПЕРЕРУ́Б, у, ч. Надмірне, '
                                                            'понад норму вирубування лісу.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Переруб, -бу, м. 1) = переріз. Желех. 2) Закром. '
                                              'Вх. Зн. 48.',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}},
             {'headword': 'переру́б',
              'short_label': 'вирубування лісу понад встановлену норму (ліс.)',
              'gloss': 'overlogging, felling timber in excess of allowable annual cut (forestry)',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[pɛrɛˈrub]'},
              'stress': {'form': 'переру́б',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/переруб'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'переру́б',
                                                                 'plural': 'переру́би'},
                                                    'родовий': {'singular': 'переру́бу',
                                                                'plural': 'переру́бів'},
                                                    'давальний': {'singular': 'переру́бу',
                                                                  'plural': 'переру́бам'},
                                                    'знахідний': {'singular': 'переру́б',
                                                                  'plural': 'переру́би'},
                                                    'орудний': {'singular': 'переру́бом',
                                                                'plural': 'переру́бами'},
                                                    'місцевий': {'singular': 'переру́бі',
                                                                 'plural': 'переру́бах'},
                                                    'кличний': {'singular': 'переру́бе',
                                                                'plural': 'переру́би'}}}},
              'distinction_note': 'Означає «надмірне, понад норму вирубування лісу (лісове '
                                  'господарство)». Не плутати з «пере́руб» (засік у коморі).',
              'meaning': {'definitions': ['Надмірне, понад затверджену норму вирубування лісових '
                                          'масивів.'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ПЕРЕРУ́Б, у, ч. Надмірне, понад норму '
                                                            'вирубування лісу. В карпатських лісах '
                                                            'допускаються значні переруби, що може '
                                                            'негативно позначитись на лісовій '
                                                            'промисловості (Рад. Укр., 14.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}}],
 'попадати': [{'headword': 'попа́дати',
               'short_label': 'упасти один за одним або всім разом (док.)',
               'gloss': 'fall down one after another or all at once (of many people or things, '
                        'perf.)',
               'pos': 'verb',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈpɑdɐtɪ]'},
               'stress': {'form': 'попа́дати',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/попадати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «упасти один за одним про багатьох або багато '
                                   'чого-небудь (док. до падати)». Не плутати з «попада́ти» '
                                   '(недоконаний вид: влучати в ціль).',
               'meaning': {'definitions': ['Упасти один за одним або всім разом (про багатьох осіб '
                                           'чи предмети; доконаний вид).'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОПА́ДАТИ, аємо, аєте, док. 1. '
                                                             'Упасти один за одним (про багатьох, '
                                                             'багато чого-небудь). — А ми втечемо. '
                                                             '— А ми доженемо.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Попадати, -даємо, -єте, гл. Упасть (о многих).',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}},
              {'headword': 'попада́ти',
               'short_label': 'влучати в ціль або опинятися десь (недок.)',
               'gloss': 'hit a target, strike a mark or find oneself somewhere (imperfective)',
               'pos': 'verb',
               'cefr': 'A2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔpɐˈdɑtɪ]'},
               'stress': {'form': 'попада́ти',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/попадати'},
               'morphology': {'pos': 'дієслово',
                              'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': 'Означає «кидаючи щось або стріляючи, досягати цілі, влучати; '
                                   'опинятися десь (недок. до попасти)». Не плутати з доконаним '
                                   '«попа́дати» (падати багатьом).',
               'meaning': {'definitions': ['Кидаючи щось або стріляючи, досягати цілі, влучати; '
                                           'опинятися в певних умовах.'],
                           'source': 'Грінченко (1907) / ВТС / СУМ-11'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОПАДА́ТИ, а́ю, а́єш, недок., '
                                                             'ПОПА́СТИ, аду́, аде́ш, док. 1. '
                                                             'перех. і неперех., у кого-що, кому. '
                                                             'Кидаючи щось або стріляючи, досягати '
                                                             'цілі; влучати.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період '
                                                                  '(СУМ-11). Наведено для '
                                                                  'лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Попадати 2, -дАю, -єш, сов. в. попасти, -падУ, '
                                               '-деш, гл. Попадать, попасть, поймать, захватить.',
                                      'historical_note': 'Автентичне народне мововживання, '
                                                         'зафіксоване Борисом Грінченком в умовах '
                                                         'дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та '
                                                         'Емського указу 1876 р.).'}}],
 'посипатися': [{'headword': 'поси́патися',
                 'short_label': 'раптово обвалитися або полетіти донизу сипкою масою (док.)',
                 'gloss': 'spill out, come tumbling or showering down, crumble (perf.)',
                 'pos': 'verb',
                 'cefr': 'B1',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔˈsɪpɐtɪsʲɐ]'},
                 'stress': {'form': 'поси́патися',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/посипатися'},
                 'morphology': {'pos': 'дієслово',
                                'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Означає «почати сипатися, вільно падати сипкою масою; '
                                     'обвалитися (док.)». Не плутати з недоконаним «посипа́тися» '
                                     '(покриватися порошком).',
                 'meaning': {'definitions': ['Почати сипатися, вільно падати (про сипкі або дрібні '
                                             'предмети; доконаний вид).'],
                             'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОСИ́ПАТИСЯ, плеться, док. 1. '
                                                               'Почати сипатися, вільно падати '
                                                               '(про що-небудь сипке або дрібне).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Посипатися, -плюся, -ллєшся, гл. Посыпаться. '
                                                 'Чорт як свиснув, то аж листя посипалось. Рудч. '
                                                 'Ск. І. 68.',
                                        'historical_note': 'Автентичне народне мововживання, '
                                                           'зафіксоване Борисом Грінченком в '
                                                           'умовах дії антиукраїнських імперських '
                                                           'указів (Валуєвського циркуляра 1863 р. '
                                                           'та Емського указу 1876 р.).'}},
                {'headword': 'посипа́тися',
                 'short_label': 'покриватися порошком, піском чи сіллю (пас., недок.)',
                 'gloss': 'be sprinkled, dusted or covered with powder/grains (passive, imperf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔsɪˈpɑtɪsʲɐ]'},
                 'stress': {'form': 'посипа́тися',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/посипатися'},
                 'morphology': {'pos': 'дієслово',
                                'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Означає «бути посипаним порошком, сіллю чи піском (пасивний '
                                     'стан до посипати, недок.)». Не плутати з активним доконаним '
                                     '«поси́патися» (обвалитися).',
                 'meaning': {'definitions': ['Пасивний стан до посипа́ти: покриватися зверху '
                                             'сипкою речовиною.'],
                             'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОСИПА́ТИСЯ, а́ється, недок. Пас. '
                                                               'до посипа́ти 4.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський '
                                                                    'період (СУМ-11). Наведено для '
                                                                    'лексикографічної '
                                                                    'прозорості.'}}],
 'пригар': [{'headword': 'при́гар',
             'short_label': 'запах, присмак або слід пригорілої страви (розм., діал.)',
             'gloss': 'burnt smell, scorched taste or crust of food (colloquial, dialectal)',
             'pos': 'noun',
             'cefr': 'B2',
             'heritage_status': {'classification': 'authentic-dialectism',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[ˈprɪɦɐr]'},
             'stress': {'form': 'при́гар',
                        'source': 'Грінченко (1907) / ВТС',
                        'url': 'https://slovnyk.me/dict/vts/пригар'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'чоловічий',
                                         'animacy': 'inanimate',
                                         'cases': {'називний': {'singular': 'при́гар',
                                                                'plural': 'при́гари'},
                                                   'родовий': {'singular': 'при́гару',
                                                               'plural': 'при́гарів'},
                                                   'давальний': {'singular': 'при́гару',
                                                                 'plural': 'при́гарам'},
                                                   'знахідний': {'singular': 'при́гар',
                                                                 'plural': 'при́гари'},
                                                   'орудний': {'singular': 'при́гаром',
                                                               'plural': 'при́гарами'},
                                                   'місцевий': {'singular': 'при́гарі',
                                                                'plural': 'при́гарах'},
                                                   'кличний': {'singular': 'при́гаре',
                                                               'plural': 'при́гари'}}}},
             'distinction_note': 'Означає «те саме, що пригара (запах або присмак пригорілого; '
                                 'пригоріла кірка куховарства)». Не плутати з металургійним '
                                 '«прига́р» (спіклийся шар піску на виливку).',
             'meaning': {'definitions': ['Те саме, що прига́ра: запах, присмак або шматочки '
                                         'пригорілої їжі.'],
                         'source': 'Грінченко (1907) / ВТС / СУМ-11'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'ПРИ́ГАР, у, ч. і ж., діал. Те саме, що '
                                                           'прига́ра. ПРИГА́Р, у, ч. Те, що '
                                                           'пригоріло, пристало до поверхні (при '
                                                           'варінні, плавленні і т. ін.).',
                                             'sovietization_risk': 0,
                                             'keywords': [],
                                             'historical_note': 'Зафіксовано в радянський період '
                                                                '(СУМ-11). Наведено для '
                                                                'лексикографічної прозорості.'},
             'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                    'quote': 'Пригара, -ри, ж. 1) Пригорелыя части кушанья. 2) '
                                             'Сивушное масло, гарь (о водке). Одгонить пригарами '
                                             'горілка. Н. Вол. у.',
                                    'historical_note': 'Автентичне народне мововживання, '
                                                       'зафіксоване Борисом Грінченком в умовах '
                                                       'дії антиукраїнських імперських указів '
                                                       '(Валуєвського циркуляра 1863 р. та '
                                                       'Емського указу 1876 р.).'}},
            {'headword': 'прига́р',
             'short_label': 'припечений шар формувальної суміші на виливку (техн.)',
             'gloss': 'scab, burnt sand crust on a metal casting surface (metallurgy)',
             'pos': 'noun',
             'cefr': 'B2',
             'heritage_status': {'classification': 'standard',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[prɪˈɦɑr]'},
             'stress': {'form': 'прига́р',
                        'source': 'ВТС / СУМ-11',
                        'url': 'https://slovnyk.me/dict/vts/пригар'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'чоловічий',
                                         'animacy': 'inanimate',
                                         'cases': {'називний': {'singular': 'прига́р',
                                                                'plural': 'прига́ри'},
                                                   'родовий': {'singular': 'прига́ру',
                                                               'plural': 'прига́рів'},
                                                   'давальний': {'singular': 'прига́ру',
                                                                 'plural': 'прига́рам'},
                                                   'знахідний': {'singular': 'прига́р',
                                                                 'plural': 'прига́ри'},
                                                   'орудний': {'singular': 'прига́ром',
                                                               'plural': 'прига́рами'},
                                                   'місцевий': {'singular': 'прига́рі',
                                                                'plural': 'прига́рах'},
                                                   'кличний': {'singular': 'прига́ре',
                                                               'plural': 'прига́ри'}}}},
             'distinction_note': 'Означає «те, що пригоріло, міцно пристало до металевої поверхні '
                                 'виливка при литті (техн.)». Не плутати з побутовим кулінарним '
                                 '«при́гар».',
             'meaning': {'definitions': ['Те, що пригоріло, пристало до поверхні металу при '
                                         'плавленні чи варінні (техн.).'],
                         'source': 'ВТС / СУМ-11'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'ПРИГА́Р, у, ч. Те, що пригоріло, '
                                                           'пристало до поверхні (при варінні, '
                                                           'плавленні і т. ін.).',
                                             'sovietization_risk': 0,
                                             'keywords': [],
                                             'historical_note': 'Зафіксовано в радянський період '
                                                                '(СУМ-11). Наведено для '
                                                                'лексикографічної прозорості.'}}],
 'провозити': [{'headword': 'прово́зити',
                'short_label': 'транспортувати крізь щось або повз якийсь пункт (недок.)',
                'gloss': 'convey past, transport through a checkpoint or territory (imperfective)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɔˈwɔzɪtɪ]'},
                'stress': {'form': 'прово́зити',
                           'source': 'Грінченко (1907) / ВТС',
                           'url': 'https://slovnyk.me/dict/vts/провозити'},
                'morphology': {'pos': 'дієслово',
                               'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': 'Означає «везучи, переміщати крізь щось або повз когось '
                                    '(недок. до провезти)». Не плутати з доконаним «провози́ти» '
                                    '(возити якийсь час або якусь кількість).',
                'meaning': {'definitions': ['Везучи, переміщати кого-, що-небудь повз якийсь пункт '
                                            'чи через кордон (недок.).'],
                            'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРОВО́ЗИТИ, о́жу, о́зиш, недок., '
                                                              'ПРОВЕЗТИ́, зу́, зе́ш; мин. ч. '
                                                              'прові́з, везла́, ло́; док., перех. '
                                                              'Везучи, переміщати кого-, '
                                                              'що-небудь.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної прозорості.'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'Провозити, -жу, -зиш, сов. в. провезти, -зу, '
                                                '-зЕш, гл. Провозить, провезти. Верстви зо дві я '
                                                'його провіз, а, там він уже сам пішов. Харьк. у.',
                                       'historical_note': 'Автентичне народне мововживання, '
                                                          'зафіксоване Борисом Грінченком в умовах '
                                                          'дії антиукраїнських імперських указів '
                                                          '(Валуєвського циркуляра 1863 р. та '
                                                          'Емського указу 1876 р.).'}},
               {'headword': 'провози́ти',
                'short_label': 'возити когось чи щось певний проміжок часу або кількість (док.)',
                'gloss': 'spend time transporting, haul around for a certain duration (perf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɔwɔˈzɪtɪ]'},
                'stress': {'form': 'провози́ти',
                           'source': 'ВТС / СУМ-11',
                           'url': 'https://slovnyk.me/dict/vts/провозити'},
                'morphology': {'pos': 'дієслово',
                               'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає «возити якийсь час або якусь кількість (доконаний '
                                    'вид: провозити поранених усю ніч)». Не плутати з недоконаним '
                                    '«прово́зити».',
                'meaning': {'definitions': ['Возити якийсь час або певну кількість (доконаний '
                                            'вид).'],
                            'source': 'ВТС / СУМ-11'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРОВОЗИ́ТИ, ожу́, о́зиш, док., '
                                                              'перех. Возити якийсь час або якусь '
                                                              'кількість.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський '
                                                                   'період (СУМ-11). Наведено для '
                                                                   'лексикографічної '
                                                                   'прозорості.'}}],
 'розбігатися': [{'headword': 'розбі́гатися',
                  'short_label': 'почати неспокійно бігати, метушитися (розм., док.)',
                  'gloss': 'start running around excitedly, bustle about restlessly (colloquial, '
                           'perf.)',
                  'pos': 'verb',
                  'cefr': 'B1',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[rɔzˈbiɦɐtɪsʲɐ]'},
                  'stress': {'form': 'розбі́гатися',
                             'source': 'Грінченко (1907) / ВТС',
                             'url': 'https://slovnyk.me/dict/vts/розбігатися'},
                  'morphology': {'pos': 'дієслово',
                                 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає «почати багато бігати, метушитися або розігнатися '
                                      'перед стрибком (розм., док.)». Не плутати з «розбіга́тися» '
                                      '(недоконаний вид: розбігатися врізнобіч).',
                  'meaning': {'definitions': ['Почати багато бігати, метушитися (розм., доконаний '
                                              'вид).'],
                              'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'РОЗБІ́ГАТИСЯ, аюся, аєшся, док., '
                                                                'розм. Почати багато бігати. — Вже '
                                                                'правда, що розбігалась, як курка '
                                                                'з яйцем, — не дала гаразд і '
                                                                'виспатись.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський '
                                                                     'період (СУМ-11). Наведено '
                                                                     'для лексикографічної '
                                                                     'прозорості.'},
                  'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                         'quote': 'Розбігатися 2, -гаюся, -єшся, гл. Разбегаться. '
                                                  'Чого це ти так розбігався сьогодня?',
                                         'historical_note': 'Автентичне народне мововживання, '
                                                            'зафіксоване Борисом Грінченком в '
                                                            'умовах дії антиукраїнських імперських '
                                                            'указів (Валуєвського циркуляра 1863 '
                                                            'р. та Емського указу 1876 р.).'}},
                 {'headword': 'розбіга́тися',
                  'short_label': 'розсіюватися в різні боки або розходитися променями (недок.)',
                  'gloss': 'scatter in all directions, disperse, radiate outward (imperfective)',
                  'pos': 'verb',
                  'cefr': 'A2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[rɔzbiˈɦɑtɪsʲɐ]'},
                  'stress': {'form': 'розбіга́тися',
                             'source': 'Грінченко (1907) / ВТС',
                             'url': 'https://slovnyk.me/dict/vts/розбігатися'},
                  'morphology': {'pos': 'дієслово',
                                 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Означає «дуже швидко рушати, розходитися в різні боки; '
                                      'розсіюватися (недок. до розбігтися)». Не плутати з '
                                      'доконаним «розбі́гатися».',
                  'meaning': {'definitions': ['Рушати, розходитися або розлітатися з одного місця '
                                              'в різні боки (недоконаний вид).'],
                              'source': 'Грінченко (1907) / ВТС / СУМ-11'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'РОЗБІГА́ТИСЯ, а́юся, а́єшся, '
                                                                'недок., РОЗБІ́ГТИСЯ, біжу́ся, '
                                                                'біжи́шся, док. 1. Дуже швидко '
                                                                'рушати, розходитися з одного '
                                                                'місця в різні боки, місця (про '
                                                                'всіх або багатьох). Палажка '
                                                                'кидалась до Кайдашихи й била '
                                                                'кулаком об кулак.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський '
                                                                     'період (СУМ-11). Наведено '
                                                                     'для лексикографічної '
                                                                     'прозорості.'},
                  'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                         'quote': 'Розбігатися 1, -гАюся, -єшся, сов. в. '
                                                  'розбігтися, -жуся, -жишся, гл. 1) Разбегаться, '
                                                  'разбежаться в разныя стороны.',
                                         'historical_note': 'Автентичне народне мововживання, '
                                                            'зафіксоване Борисом Грінченком в '
                                                            'умовах дії антиукраїнських імперських '
                                                            'указів (Валуєвського циркуляра 1863 '
                                                            'р. та Емського указу 1876 р.).'}}],
 'рябець': [{'headword': 'ря́бець',
             'short_label': 'хижий птах шуліка або вид рябого метелика (розм.)',
             'gloss': 'black kite / bird of prey or checkered butterfly (colloquial)',
             'pos': 'noun',
             'cefr': 'B2',
             'heritage_status': {'classification': 'standard',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[ˈrʲɑbɛt͡sʲ]'},
             'stress': {'form': 'ря́бець',
                        'source': 'Грінченко (1907) / ВТС',
                        'url': 'https://slovnyk.me/dict/vts/рябець'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'чоловічий',
                                         'animacy': 'animate',
                                         'cases': {'називний': {'singular': 'ря́бець',
                                                                'plural': 'ря́бці'},
                                                   'родовий': {'singular': 'ря́бця',
                                                               'plural': 'ря́бців'},
                                                   'давальний': {'singular': 'ря́бцеві',
                                                                 'plural': 'ря́бцям'},
                                                   'знахідний': {'singular': 'ря́бця',
                                                                 'plural': 'ря́бців'},
                                                   'орудний': {'singular': 'ря́бцем',
                                                               'plural': 'ря́бцями'},
                                                   'місцевий': {'singular': 'ря́бцеві',
                                                                'plural': 'ря́бцях'},
                                                   'кличний': {'singular': 'ря́бцю',
                                                               'plural': 'ря́бці'}}}},
             'distinction_note': 'Означає «те саме, що шуліка (хижий птах рябого забарвлення) або '
                                 'метелик рябець». Не плутати з «рябе́ць» (лісовий птах рябчик '
                                 'Tetrastes bonasia).',
             'meaning': {'definitions': ['Те саме, що шулі́ка (хижий птах); вид метелика (розм.).'],
                         'source': 'Грінченко (1907) / ВТС / СУМ-11'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'РЯ́БЕЦЬ, бця, ч., розм. Те саме, що '
                                                           'шулі́ка. Не втекти бідасі '
                                                           '[ластівочці]: Скоро зрадить сила; '
                                                           'Бистре око в рябця І міцніші крила.',
                                             'sovietization_risk': 0,
                                             'keywords': [],
                                             'historical_note': 'Зафіксовано в радянський період '
                                                                '(СУМ-11). Наведено для '
                                                                'лексикографічної прозорості.'},
             'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                    'quote': 'Рябець, -бця, м. Род коршуна. Так рябцем і вхопить. '
                                             'Ном. № 13678.',
                                    'historical_note': 'Автентичне народне мововживання, '
                                                       'зафіксоване Борисом Грінченком в умовах '
                                                       'дії антиукраїнських імперських указів '
                                                       '(Валуєвського циркуляра 1863 р. та '
                                                       'Емського указу 1876 р.).'}},
            {'headword': 'рябе́ць',
             'short_label': 'лісовий птах родини фазанових (рябчик Tetrastes bonasia)',
             'gloss': 'hazel grouse (Tetrastes bonasia, forest gamebird of the pheasant family)',
             'pos': 'noun',
             'cefr': 'B1',
             'heritage_status': {'classification': 'standard',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[rʲɐˈbɛt͡sʲ]'},
             'stress': {'form': 'рябе́ць',
                        'source': 'ВТС / СУМ-11',
                        'url': 'https://slovnyk.me/dict/vts/рябець'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'чоловічий',
                                         'animacy': 'animate',
                                         'cases': {'називний': {'singular': 'рябе́ць',
                                                                'plural': 'рябці́'},
                                                   'родовий': {'singular': 'рябця́',
                                                               'plural': 'рябці́в'},
                                                   'давальний': {'singular': 'рябце́ві',
                                                                 'plural': 'рябця́м'},
                                                   'знахідний': {'singular': 'рябця́',
                                                                 'plural': 'рябці́в'},
                                                   'орудний': {'singular': 'рябце́м',
                                                               'plural': 'рябця́ми'},
                                                   'місцевий': {'singular': 'рябце́ві',
                                                                'plural': 'рябця́х'},
                                                   'кличний': {'singular': 'рябцю́',
                                                               'plural': 'рябці́'}}}},
             'distinction_note': 'Означає «те саме, що ря́бчик (лісовий птах родини фазанових)». '
                                 'Не плутати з «ря́бець» (шуліка).',
             'meaning': {'definitions': ['Те саме, що ря́бчик: лісовий дикий птах.'],
                         'source': 'ВТС / СУМ-11'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'РЯБЕ́ЦЬ, бця́, ч. Те саме, що ря́бчик '
                                                           '1. Іванов згадав, що.. лежить вбитий '
                                                           'ним ще вранці рябець. Він витяг його і '
                                                           'почав скубти (Багмут, Опов., 1959, '
                                                           '45); *У порівн. Кінь під ним сірий, як '
                                                           'рябець (П.',
                                             'sovietization_risk': 0,
                                             'keywords': [],
                                             'historical_note': 'Зафіксовано в радянський період '
                                                                '(СУМ-11). Наведено для '
                                                                'лексикографічної прозорості.'}}],
 'травник': [{'headword': 'тра́вник',
              'short_label': 'гербарій рослин або старовинний травник-порадник',
              'gloss': 'herbarium or ancient herbal guide / pharmacopoeia of medicinal plants',
              'pos': 'noun',
              'cefr': 'B1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈtrɑwnɪk]'},
              'stress': {'form': 'тра́вник',
                         'source': 'ВТС / СУМ-11',
                         'url': 'https://slovnyk.me/dict/vts/травник'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'тра́вник',
                                                                 'plural': 'тра́вники'},
                                                    'родовий': {'singular': 'тра́вника',
                                                                'plural': 'тра́вників'},
                                                    'давальний': {'singular': 'тра́внику',
                                                                  'plural': 'тра́вникам'},
                                                    'знахідний': {'singular': 'тра́вник',
                                                                  'plural': 'тра́вники'},
                                                    'орудний': {'singular': 'тра́вником',
                                                                'plural': 'тра́вниками'},
                                                    'місцевий': {'singular': 'тра́внику',
                                                                 'plural': 'тра́вниках'},
                                                    'кличний': {'singular': 'тра́внику',
                                                                'plural': 'тра́вники'}}}},
              'distinction_note': 'Означає «гербарій рослин або старовинна книжка про лікувальні '
                                  "трави (травник, фармакопея)». Не плутати з «травни́к» (трав'яна "
                                  'настоянка або зарослий травою моріг).',
              'meaning': {'definitions': ['Гербарій; старовинна книга з описом цілющих рослин та '
                                          'ліків.'],
                          'source': 'ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ТРА́ВНИК, а, ч. 1. Те саме, що '
                                                            'герба́рій 1. 2. заст. Книжка, в якій '
                                                            'спочатку описувались лікувальні '
                                                            'рослини, а згодом давались поради, як '
                                                            'їх використовувати. У Стародавній '
                                                            'Русі укладали спеціальні збірники, '
                                                            'травники.., а в XVI-XVII ст.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'}},
             {'headword': 'травни́к',
              'short_label': "трав'яна настоянка на горілці або ділянка, поросла травою",
              'gloss': 'herbal tincture / liqueur or grassy plot / lawn (colloquial)',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[trɐwˈnɪk]'},
              'stress': {'form': 'травни́к',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/травник'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'травни́к',
                                                                 'plural': 'травники́'},
                                                    'родовий': {'singular': 'травнику́',
                                                                'plural': 'травникі́в'},
                                                    'давальний': {'singular': 'травнику́',
                                                                  'plural': 'травника́м'},
                                                    'знахідний': {'singular': 'травни́к',
                                                                  'plural': 'травники́'},
                                                    'орудний': {'singular': 'травнико́м',
                                                                'plural': 'травника́ми'},
                                                    'місцевий': {'singular': 'травнику́',
                                                                 'plural': 'травника́х'},
                                                    'кличний': {'singular': 'травнику́',
                                                                'plural': 'травники́'}}}},
              'distinction_note': 'Означає «настоянка на цілющих травах (розм.) або ділянка, густо '
                                  'вкрита травою (моріг)». Не плутати з книгою/гербарієм '
                                  '«тра́вник».',
              'meaning': {'definitions': ['Настоянка на травах (розм.); місце, поросле травою.'],
                          'source': 'Грінченко (1907) / ВТС / СУМ-11'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ТРАВНИ́К, ч., розм. 1. род. у́. '
                                                            'Настоянка на травах. 2. род. а́, '
                                                            'рідко. Місце, поросле травою.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період '
                                                                 '(СУМ-11). Наведено для '
                                                                 'лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Травник, -ка, м. Место поросшее травой. Стану з '
                                              'тобов до слюбоньку на травнику-билиску. Гол. IV. '
                                              '167.',
                                     'historical_note': 'Автентичне народне мововживання, '
                                                        'зафіксоване Борисом Грінченком в умовах '
                                                        'дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та '
                                                        'Емського указу 1876 р.).'}}]}
