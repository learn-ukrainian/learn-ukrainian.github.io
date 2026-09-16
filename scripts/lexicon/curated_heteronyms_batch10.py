"""Curated heteronym dataset (Batch 10) for Word Atlas (#8039, #4387).

This module defines 32 curated heteronym lemmas (64 distinct variants)
expanding the curated heteronym SSOT from 296 to 328 lemmas.

Decolonization & Lexicographical Invariants:
1. Modern standard baseline: Academic СУМ-20 / ВТС (2005) / ULIF authorities.
2. Authentic pre-Soviet witness: Грінченко (1907–1909), compiled/published
   under Tsarist Russian imperial bans (Valuev Circular 1863, Ems Ukaz 1876).
3. Soviet colonization context: СУМ-11 (1970–1980) documented transparently
   under `soviet_colonization_context` with `sovietization_risk` and historical notes
   without erasing lexical history. All quotations are 100% contiguous verbatim excerpts
   from academic sources. СУМ-11 is strictly quarantined from normative fields.
4. Clean morphology and phonology: Every variant is morphologically verified against VESUM.
"""

from typing import Any

CURATED_HETERONYMS_BATCH_10: dict[str, list[dict[str, Any]]] = {'виїмковий': [{'headword': 'ви́їмковий',
                'short_label': 'стосовний до гірничої виїмки пластів корисної копалини',
                'gloss': 'relating to mining extraction, excavation or extraction cuts',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[ˈwɪjimkɔwɪj]'},
                'stress': {'form': 'ви́їмковий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/виїмковий'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Гірничий термін: прикметник від «ви́їмка 1» (виймання або розробка корисних '
                                    'копалин у шахті). Не плутати з «виїмко́вий» (винятковий, надзвичайний).',
                'meaning': {'definitions': ['Прикметник до ви́їмка (розробка, видалення породи чи корисних копалин у '
                                            'гірництві).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ВИ́ЇМКОВИЙ, а, е. Прикм. до ви́їмка 1. Перехід на '
                                                              'суцільну систему розробки пластів.. вимагав переглянути '
                                                              'питання про розміри виїмкових ділянок (Розв. науки в '
                                                              'УРСР.., 1957, 405).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'виїмко́вий',
                'short_label': 'винятковий, надзвичайний, особливий (заст., діал.)',
                'gloss': 'exceptional, extraordinary or singular (archaic, dialectal)',
                'pos': 'adj',
                'cefr': 'C1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[wɪjimˈkɔwɪj]'},
                'stress': {'form': 'виїмко́вий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/виїмковий'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Означає «винятковий, рідкісний, незвичайний» (західноукраїнське літературне та '
                                    'діалектне слово, уживане зокрема І. Франком). Не плутати з технічним «ви́їмковий» '
                                    '(гірнича виїмка).',
                'meaning': {'definitions': ['Те саме, що винятко́вий: надзвичайний, особливий (заст., діал.).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ВИЇМКО́ВИЙ, а, е, заст. Те саме, що винятко́вий. Куна '
                                                              'сьогодні виїмковим способом.. [залишився] аж до обіду '
                                                              'дома (Фр., II, 1950, 80).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'люковий': [{'headword': 'лю́ковий',
              'short_label': 'стосовний до люка (отвору з кришкою)',
              'gloss': 'relating to a hatch, trapdoor or manhole',
              'pos': 'adj',
              'cefr': 'B1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈlʲukɔwɪj]'},
              'stress': {'form': 'лю́ковий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/люковий'},
              'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
              'distinction_note': 'Прикметник від іменника «люк» (люковий отвір, люкова кришка). Не плутати з '
                                  'іменником «люкови́й» (робітник біля люка печі).',
              'meaning': {'definitions': ['Прикметник до люк (отвір з кришкою в підлозі, палубі, бункері).'],
                          'source': 'ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ЛЮ́КОВИЙ, а, е. Прикм. до люк. Башти [силосні] слід '
                                                            'розміщувати поблизу тваринницьких ферм люковими прорізами '
                                                            'в бік будівлі (Колг. енц., II, 1956, 480).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': None},
             {'headword': 'люкови́й',
              'short_label': 'робітник, що обслуговує люки коксових чи доменних печей',
              'gloss': 'hatch tender, furnace top operator or manhole worker',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[lʲukɔˈwɪj]'},
              'stress': {'form': 'люкови́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/люковий'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'чоловічий',
                                          'animacy': 'animate',
                                          'cases': {'називний': {'singular': 'люкови́й', 'plural': 'люкові́'},
                                                    'родовий': {'singular': 'люково́го', 'plural': 'люкови́х'},
                                                    'давальний': {'singular': 'люково́му', 'plural': 'люкови́м'},
                                                    'знахідний': {'singular': 'люково́го', 'plural': 'люкови́х'},
                                                    'орудний': {'singular': 'люкови́м', 'plural': 'люкови́ми'},
                                                    'місцевий': {'singular': 'люково́му', 'plural': 'люкови́х'},
                                                    'кличний': {'singular': 'люкови́й', 'plural': 'люкові́'}}}},
              'distinction_note': 'Субстантивований іменник: фах робітника біля люків коксової батареї чи '
                                  'металургійної печі. Не плутати з прикметником «лю́ковий» (стосовний до люка).',
              'meaning': {'definitions': ['Робітник, який обслуговує завантажувальні люки печей чи агрегатів.'],
                          'source': 'ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ЛЮКОВИ́Й, во́го, ч. Робітник, що працює біля люка певного '
                                                            'агрегату. Як солдат на чатах стоїть біля вогнедишних '
                                                            'коксових батарей один з кращих люкових.. коксохімічного '
                                                            'заводу (Рад. Укр., 30. IV 1964, 1).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': None}],
 'магістерський': [{'headword': 'магі́стерський',
                    'short_label': 'стосовний до магістра ордену чи лицарського звання (іст.)',
                    'gloss': 'relating to a grand master of a chivalric or religious order',
                    'pos': 'adj',
                    'cefr': 'B2',
                    'heritage_status': {'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                    'pronunciation': {'ipa': '[mɐˈɦistɛrsʲkɪj]'},
                    'stress': {'form': 'магі́стерський',
                               'source': 'ВТС',
                               'url': 'https://slovnyk.me/dict/vts/магістерський'},
                    'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                    'distinction_note': 'Історичний термін: стосовний до глави духовно-лицарського ордену (великого '
                                        'магістра, магістра). Не плутати з освітнім «магісте́рський» (науковий ступінь '
                                        'магістра).',
                    'meaning': {'definitions': ['Прикметник до магі́стр, магі́стер (великий магістр ордену; іст.).'],
                                'source': 'ВТС'},
                    'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'МАГІ́СТЕРСЬКИЙ, а, е, іст. Прикм. до магі́стр, '
                                                                  'магі́стер 2; належний магістрові. Магістерський '
                                                                  'титул.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                       'Наведено для лексикографічної прозорості.'},
                    'pre_soviet_witness': None},
                   {'headword': 'магісте́рський',
                    'short_label': 'стосовний до наукового ступеня або кваліфікації магістра',
                    'gloss': "relating to an academic master's degree or graduate study",
                    'pos': 'adj',
                    'cefr': 'B1',
                    'heritage_status': {'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                    'pronunciation': {'ipa': '[mɐɦisˈtɛrsʲkɪj]'},
                    'stress': {'form': 'магісте́рський',
                               'source': 'ВТС',
                               'url': 'https://slovnyk.me/dict/vts/магістерський'},
                    'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                    'distinction_note': 'Освітній термін: стосовний до наукового ступеня чи освітньої програми '
                                        'магістра (магістерська робота, магістерський диплом). Не плутати з '
                                        '«магі́стерський» (орденський магістр).',
                    'meaning': {'definitions': ['Стосовний до освітньо-наукового ступеня або звання магістра.'],
                                'source': 'ВТС'},
                    'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'МАГІСТЕ́РСЬКИЙ, а, е. Стос. до магістра (у 1 '
                                                                  'знач.). Після закінчення Лазаревського інституту '
                                                                  '[1892 р. ] він [А. Кримський] був залишений при '
                                                                  'ньому для підготовки до магістерського екзамену '
                                                                  '(Вітч., 1, 1961, 165); У 1891 році Фаворський '
                                                                  'блискуче захистив магістерську дисертацію про '
                                                                  'однозаміщені ацетиленові вуглеводні (Наука.., 3, '
                                                                  '1960, 27).',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                       'Наведено для лексикографічної прозорості.'},
                    'pre_soviet_witness': None}],
 'масничка': [{'headword': 'ма́сничка',
               'short_label': 'пестливе до масниця (свято проводів зими)',
               'gloss': 'diminutive of Masnytsia (pancake / butter carnival week)',
               'pos': 'noun',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ˈmɑsnɪt͡ʃkɐ]'},
               'stress': {'form': 'ма́сничка',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/масничка'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'ма́сничка', 'plural': 'ма́снички'},
                                                     'родовий': {'singular': 'ма́снички', 'plural': 'ма́сничок'},
                                                     'давальний': {'singular': 'ма́сничці', 'plural': 'ма́сничкам'},
                                                     'знахідний': {'singular': 'ма́сничку', 'plural': 'ма́снички'},
                                                     'орудний': {'singular': 'ма́сничкою', 'plural': 'ма́сничками'},
                                                     'місцевий': {'singular': 'ма́сничці', 'plural': 'ма́сничках'},
                                                     'кличний': {'singular': 'ма́сничко', 'plural': 'ма́снички'}}}},
               'distinction_note': 'Пестлива назва свята Масниці (відоме в приказці «Минулася котові ма́сничка»). Не '
                                   'плутати з «масни́чка» (посудина для збивання масла).',
               'meaning': {'definitions': ['Пестливе до ма́сниця (традиційне українське свято проводів зими).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'МА́СНИЧКА, и, ж., церк. Пестл. до ма́сниця. ◊ Мине́ться '
                                                             '(мину́лася, закінчи́ться, закінчи́лася і т. ін.) кото́ві '
                                                             'ма́сничка — те саме, що Мине́ться (мину́лася, '
                                                             'закінчи́ться, закінчи́лася і т. ін.) кото́ві ма́сниця ( '
                                                             'див. ма́сниця).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'МАсничка, -ки, ж. 1) Ум. от масниця. Ой, масничко, яка ти була! Як би '
                                               'тебе сім неділь, а посту одна. Грин. І. 240. 2) Маслянка (посуда для '
                                               'масла). 3) Кадка с маслом. 4) Маслобойка.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}},
              {'headword': 'масни́чка',
               'short_label': 'посудина з пристосуванням для збивання масла (маслянка)',
               'gloss': 'butter churn, container or device for churning butter',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[mɐsˈnɪt͡ʃkɐ]'},
               'stress': {'form': 'масни́чка',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/масничка'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'масни́чка', 'plural': 'масни́чки'},
                                                     'родовий': {'singular': 'масни́чки', 'plural': 'масни́чок'},
                                                     'давальний': {'singular': 'масни́чці', 'plural': 'масни́чкам'},
                                                     'знахідний': {'singular': 'масни́чку', 'plural': 'масни́чки'},
                                                     'орудний': {'singular': 'масни́чкою', 'plural': 'масни́чками'},
                                                     'місцевий': {'singular': 'масни́чці', 'plural': 'масни́чках'},
                                                     'кличний': {'singular': 'масни́чко', 'plural': 'масни́чки'}}}},
               'distinction_note': "Предметний іменник: дерев'яна або глиняна посудина для збивання масла з вершків "
                                   '(маслобійка, маслянка). Не плутати з «ма́сничка» (пестливе до свята Масниці).',
               'meaning': {'definitions': ['Посудина з колотівкою або пристосуванням для збивання масла.'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'МАСНИ́ЧКА, и, ж. Спеціальна посудина з пристосуванням '
                                                             'для збивання масла з вершків або сметани. Мама в коморі '
                                                             'за стіною все ще гуркотіла масничкою, не входила до '
                                                             'кімнати (Ков., Світ.., 1960, 8).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'МАсничка, -ки, ж. 1) Ум. от масниця. Ой, масничко, яка ти була! Як би '
                                               'тебе сім неділь, а посту одна. Грин. І. 240. 2) Маслянка (посуда для '
                                               'масла). 3) Кадка с маслом. 4) Маслобойка.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}}],
 'нагніт': [{'headword': 'на́гніт',
             'short_label': 'гноблення, важкий утиск або ярмо (діал., перен.)',
             'gloss': 'oppression, heavy burden, tyranny or downtrodden state (dialectal)',
             'pos': 'noun',
             'cefr': 'B2',
             'heritage_status': {'classification': 'standard',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[ˈnɑɦɲit]'},
             'stress': {'form': 'на́гніт',
                        'source': 'Грінченко (1907) / ВТС',
                        'url': 'https://slovnyk.me/dict/vts/нагніт'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'чоловічий',
                                         'animacy': 'inanimate',
                                         'cases': {'називний': {'singular': 'на́гніт'},
                                                   'родовий': {'singular': 'на́гніту'},
                                                   'давальний': {'singular': 'на́гнітові / на́гніту'},
                                                   'знахідний': {'singular': 'на́гніт'},
                                                   'орудний': {'singular': 'на́гнітом'},
                                                   'місцевий': {'singular': 'на́гніті'},
                                                   'кличний': {'singular': 'на́гніте'}}}},
             'distinction_note': 'Діалектне та переносне значення: гноблення, важкий утиск чи неволя (уживане І. '
                                 'Франком). Не плутати з ветеринарним терміном «нагні́т» (болячка на холці коня від '
                                 'сідла).',
             'meaning': {'definitions': ['Гноблення, важкий утиск або тягар неволі (діал., перен.).'],
                         'source': 'Грінченко (1907) / ВТС'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'НА́ГНІТ, у, ч., діал. Гноблення. В часах пониження й '
                                                           'неволі, І нагніту, і темноти.. Родився, ріс і виріс ти '
                                                           '(Фр., X, 1954, 265); Середняки, збуваючись глитайського '
                                                           'нагніту, стали поводитися вільніше (Епік, Тв., 1958, 235).',
                                             'sovietization_risk': 1,
                                             'keywords': ['глитай', 'середняк'],
                                             'historical_note': 'Радянський академічний словник СУМ-11 ілюструє '
                                                                'діалектне слово через класово-ідеологічне кліше '
                                                                'радянської пропаганди про «глитайський нагніт» і '
                                                                '«середняків».'},
             'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                    'quote': 'НАгніт, -ту, м. Натиск, давленіе. Желех.',
                                    'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                       'Грінченком в умовах дії антиукраїнських імперських указів '
                                                       '(Валуєвського циркуляра 1863 р. та Емського указу 1876 р.).'}},
            {'headword': 'нагні́т',
             'short_label': 'запалення або болячка на холці коня від збруї (вет.)',
             'gloss': 'withers gall, saddle sore or harness inflammation in horses',
             'pos': 'noun',
             'cefr': 'B2',
             'heritage_status': {'classification': 'standard',
                                 'is_russianism': False,
                                 'russian_shadow': False,
                                 'vesum_attested': True},
             'pronunciation': {'ipa': '[nɐɦˈɲit]'},
             'stress': {'form': 'нагні́т', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/нагніт'},
             'morphology': {'pos': 'іменник',
                            'paradigm': {'kind': 'noun',
                                         'gender': 'чоловічий',
                                         'animacy': 'inanimate',
                                         'cases': {'називний': {'singular': 'нагні́т'},
                                                   'родовий': {'singular': 'нагні́ту'},
                                                   'давальний': {'singular': 'нагні́тові / нагні́ту'},
                                                   'знахідний': {'singular': 'нагні́т'},
                                                   'орудний': {'singular': 'нагні́том'},
                                                   'місцевий': {'singular': 'нагні́ті'},
                                                   'кличний': {'singular': 'нагні́те'}}}},
             'distinction_note': 'Ветеринарний термін: болюче запалення тканин або рана на холці коня через погано '
                                 'припасовану збрую чи сідло. Не плутати з «на́гніт» (гноблення, утиск).',
             'meaning': {'definitions': ['Запальний процес чи потертість на холці коня від погано припасованої збруї '
                                         '(вет.).'],
                         'source': 'ВТС'},
             'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                             'definition': 'НАГНІ́Т, у, ч. Патологічні процеси переважно на холці '
                                                           'коней, що виникають від погано припасованої збруї або '
                                                           'неправильної посадки при їзді.',
                                             'sovietization_risk': 0,
                                             'keywords': [],
                                             'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                'для лексикографічної прозорості.'},
             'pre_soviet_witness': None}],
 'накликатися': [{'headword': 'накли́катися',
                  'short_label': 'багато разів кликати когось до втоми (док.)',
                  'gloss': 'call, summon or cry out to someone repeatedly until exhausted (perf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[nɐˈklɪkɐtɪsʲɐ]'},
                  'stress': {'form': 'накли́катися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/накликатися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає «багато разів кликати, втомитися кличучи (док. вид: накличуся, '
                                      'накличешся)». Не плутати з недоконаним «наклика́тися» (напрошуватися, '
                                      'добровільно зголошуватися).',
                  'meaning': {'definitions': ['Багато разів покликати або гукати кого-небудь (доконаний вид).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'НАКЛИ́КАТИСЯ, и́чуся, и́чешся, док., розм. Багато '
                                                                'разів покликати кого-небудь. Ти мене накличешся '
                                                                'ночами, Несучи розлуку за плечами, І навиглядаєшся '
                                                                'одна (Мал., Звенигора, 1959, 119).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'наклика́тися',
                  'short_label': 'напрошуватися, добровільно зголошуватися на щось (недок.)',
                  'gloss': 'volunteer, offer oneself willingly or invite oneself (imperf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[nɐklɪˈkɑtɪsʲɐ]'},
                  'stress': {'form': 'наклика́тися',
                             'source': 'Грінченко (1907) / ВТС',
                             'url': 'https://slovnyk.me/dict/vts/накликатися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Означає «напрошуватися, добровільно виявляти бажання взяти участь у чомусь '
                                      '(недок. вид: накликаюся, накликаєшся)». Не плутати з доконаним «накли́катися» '
                                      '(накликати когось багато разів).',
                  'meaning': {'definitions': ['Добровільно зголошуватися, виявляти бажання взяти участь; напрошуватися '
                                              '(недоконаний вид).'],
                              'source': 'Грінченко (1907) / ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'НАКЛИКА́ТИСЯ, а́ється, недок. 1. Добровільно виражати '
                                                                'бажання діяти в певному напрямку, добиватися '
                                                                'чого-небудь; напрошуватися. Параска, котра було '
                                                                'проходить ні з ким не поздоровкаючись, одходить — не '
                                                                'прощаючись, гордує людьми, тепер Параска сама '
                                                                'накликається, сама йде побалакати між людьми (Мирний, '
                                                                'IV, 1955, 102). 2. Пас. до наклика́ти.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                         'quote': 'НаклИкатися, -чуся, -чешся, гл. Назваться, напроситься.',
                                         'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                            'Грінченком в умовах дії антиукраїнських імперських указів '
                                                            '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                            'р.).'}}],
 'наривний': [{'headword': 'нари́вний',
               'short_label': 'стосовний до нариву (гнійника, абсцесу)',
               'gloss': 'pertaining to an abscess, boil or festering sore',
               'pos': 'adj',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐˈrɪwnɪj]'},
               'stress': {'form': 'нари́вний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/наривний'},
               'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
               'distinction_note': 'Прикметник від іменника «нари́в» (наривний стан, наривна пухлина). Не плутати з '
                                   '«наривни́й» (лікувальний засіб або пластир, що витягує гній).',
               'meaning': {'definitions': ['Прикметник до нари́в (гнійне вогнище, фурункул, абсцес).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАРИ́ВНИЙ, а, е. Прикм. до нари́в.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'наривни́й',
               'short_label': 'який витягує гній або викликає нарив (про мазь/пластир)',
               'gloss': 'blister-drawing, suppurative or healing (of medicinal plaster)',
               'pos': 'adj',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐrɪwˈnɪj]'},
               'stress': {'form': 'наривни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/наривний'},
               'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
               'distinction_note': 'Медичний термін: лікарський засіб (пластир, мазь), призначений для лікування '
                                   'наривів чи витягування гною (наривний пластир). Не плутати з «нари́вний» '
                                   '(стосовний до нариву).',
               'meaning': {'definitions': ['Який використовують при лікуванні наривів або для витягування гною '
                                           '(наривний пластир).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАРИВНИ́Й, а́, е́. Який використовують при лікуванні '
                                                             'наривів. Наривний пластир.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'наслухатися': [{'headword': 'наслу́хатися',
                  'short_label': 'почути багато чогось або задовольнити слух (док.)',
                  'gloss': "hear a great deal, listen to one's fill or hear plenty of (perf.)",
                  'pos': 'verb',
                  'cefr': 'B1',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[nɐˈsluxɐtɪsʲɐ]'},
                  'stress': {'form': 'наслу́хатися',
                             'source': 'Грінченко (1907) / ВТС',
                             'url': 'https://slovnyk.me/dict/vts/наслухатися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає «почути багато новин чи пліток, досхочу наслухатися співу чи музики '
                                      '(доконаний вид)». Не плутати з недоконаним «наслуха́тися» (напружено '
                                      'вслухатися, прислухатися).',
                  'meaning': {'definitions': ['Почути, послухати багато чого-небудь; повністю задовольнитися слуханням '
                                              '(доконаний вид).'],
                              'source': 'Грінченко (1907) / ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'НАСЛУ́ХАТИСЯ, аюся, аєшся, док., перех. 1. Почути, '
                                                                'послухати багато чого-небудь або про кого-, '
                                                                'що-небудь. Він тілько наслухався про неї [гадюку] '
                                                                'всякої страховини, і як вона кусається, і як сичить, '
                                                                'і яка страшна-страшна (Мирний, IV, 1955, 12); '
                                                                'Наслухавшись від дорослих розмов про Каховку, Данько '
                                                                'щедро оповивав її серпанком власних мрій (Гончар, І, '
                                                                '1959, 6). 2. Повністю задовольнятися, слухаючи кого-, '
                                                                'що-небудь. [Таня:] Оце наслухалась щедрівок, то й '
                                                                'здається мені, немов у селі стало диво (Вас., III, '
                                                                '1960, 125); Говорив [Сеспель] і не міг наговоритись, '
                                                                'вслухався в звуки рідної мови і не міг наслухатись '
                                                                '(Збан., Сеспель, 1961, 441); Панаса не годуй — тільки '
                                                                'дай наслухатися пісень! (Мартич, Повість про нар. '
                                                                'артиста, 1954, 22).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                         'quote': 'Наслухатися, -хаюся, -єшся, гл. Наслушаться. Наслухаєшся вже '
                                                  'всього. Рудч.',
                                         'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                            'Грінченком в умовах дії антиукраїнських імперських указів '
                                                            '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                            'р.).'}},
                 {'headword': 'наслуха́тися',
                  'short_label': 'напружено прислухатися, намагаючись почути (недок., розм.)',
                  'gloss': "strain one's ears to listen, listen attentively or eavesdrop (imperf.)",
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[nɐslʊˈxɑtɪsʲɐ]'},
                  'stress': {'form': 'наслуха́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/наслухатися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Розмовне дієслово: напружувати слух, насторожено прислухатися до звуків, гомону '
                                      'чи розмов (недоконаний вид). Не плутати з доконаним «наслу́хатися» (почути '
                                      'всього вдосталь).',
                  'meaning': {'definitions': ['Напружуючи слух, старатися почути що-небудь; прислухатися (недоконаний '
                                              'вид).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'НАСЛУХА́ТИСЯ, а́юся, а́єшся, недок., розм. '
                                                                'Напружуючись, старатися почути що-небудь; '
                                                                'прислухатися. [Старшина:] А ти, Гершку, все-таки '
                                                                'наслухайся, що там горлата голота базіка (К.-Карий, '
                                                                'І, 1960, 38); Батько підходить до дверей спальні, '
                                                                'наставляє туди вуха, наслухається (Д. Бедзик, Ост. '
                                                                'вальс, 1959, 5).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'натруска': [{'headword': 'на́труска',
               'short_label': 'старовинний ріг-порохівниця для насипання пороху (іст.)',
               'gloss': 'powder horn or priming flask for historic muskets (hist.)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ˈnɑtruskɐ]'},
               'stress': {'form': 'на́труска',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/натруска'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'на́труска', 'plural': 'на́труски'},
                                                     'родовий': {'singular': 'на́труски', 'plural': 'на́трусок'},
                                                     'давальний': {'singular': 'на́трусці', 'plural': 'на́трускам'},
                                                     'знахідний': {'singular': 'на́труску', 'plural': 'на́труски'},
                                                     'орудний': {'singular': 'на́трускою', 'plural': 'на́трусками'},
                                                     'місцевий': {'singular': 'на́трусці', 'plural': 'на́трусках'},
                                                     'кличний': {'singular': 'на́труско', 'plural': 'на́труски'}}}},
               'distinction_note': 'Історичний козацький та мисливський термін: ріжок для тонкого пороху, що насипався '
                                   "на полку старовинної крем'яної рушниці. Не плутати з віддієслівним «натру́ска» "
                                   '(дія за значенням натрусити; покарання).',
               'meaning': {'definitions': ['Посудина (ріг), з якої насипали порох на поличку стародавньої гвинтівки '
                                           '(іст.).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НА́ТРУСКА, и, ж., іст. Посудина (ріг), з якої насипали '
                                                             'порох на поличку стародавньої гвинтівки; '
                                                             'ріг-порохівниця.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Натруска, -ки, ж. 1) Зерна хлеба, смешанныя с битой (после молотьбы) '
                                               'соломой. 2) Рог с порохом для насыпки на полку ружья пороху.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}},
              {'headword': 'натру́ска',
               'short_label': 'дія за значенням натрусити; перен. суворе покарання',
               'gloss': 'sprinkling or spilling; figuratively stern reprimand or scolding',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[nɐˈtruskɐ]'},
               'stress': {'form': 'натру́ска', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/натруска'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'натру́ска', 'plural': 'натру́ски'},
                                                     'родовий': {'singular': 'натру́ски', 'plural': 'натру́сок'},
                                                     'давальний': {'singular': 'натру́сці', 'plural': 'натру́скам'},
                                                     'знахідний': {'singular': 'натру́ску', 'plural': 'натру́ски'},
                                                     'орудний': {'singular': 'натру́скою', 'plural': 'натру́сками'},
                                                     'місцевий': {'singular': 'натру́сці', 'plural': 'натру́сках'},
                                                     'кличний': {'singular': 'натру́ско', 'plural': 'натру́ски'}}}},
               'distinction_note': 'Віддієслівний іменник від «натруси́ти» (насипання, просипання); переносно — сувора '
                                   'догана, прочуханка («задати натруски»). Не плутати з козацьким предметним '
                                   '«на́труска» (ріг-порохівниця).',
               'meaning': {'definitions': ['Дія за значенням натруси́ти; перен. суворе покарання, прочуханка (розм.).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'НАТРУ́СКА, и, ж., розм. 1. Дія за знач. натруси́ти. 2. '
                                                             'перен. Суворе покарання; нагінка, прочуханка. Щоб часом '
                                                             'не було натруски від старших (Кв.-Осн., II, 1956, 160).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'невигідність': [{'headword': 'неви́гідність',
                   'short_label': 'незручність, дискомфорт, брак побутових вигод',
                   'gloss': 'inconvenience, discomfort or lack of ease',
                   'pos': 'noun',
                   'cefr': 'B1',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[nɛˈwɪɦʲidnʲisʲtʲ]'},
                   'stress': {'form': 'неви́гідність',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/невигідність'},
                   'morphology': {'pos': 'іменник',
                                  'paradigm': {'kind': 'noun',
                                               'gender': 'жіночий',
                                               'animacy': 'inanimate',
                                               'cases': {'називний': {'singular': 'неви́гідність'},
                                                         'родовий': {'singular': 'неви́гідності'},
                                                         'давальний': {'singular': 'неви́гідності'},
                                                         'знахідний': {'singular': 'неви́гідність'},
                                                         'орудний': {'singular': 'неви́гідністю'},
                                                         'місцевий': {'singular': 'неви́гідності'},
                                                         'кличний': {'singular': 'неви́гідносте'}}}},
                   'distinction_note': 'Позначає брак побутових або фізичних зручностей (незручне помешкання, '
                                       'незручний графік). Не плутати з «невигі́дність» (збитковість, відсутність '
                                       'матеріальної вигоди).',
                   'meaning': {'definitions': ['Властивість за значенням неви́гідний (позбавлений зручностей, '
                                               'незручний).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НЕВИ́ГІДНІСТЬ, ності, ж. Абстр. ім. до неви́гідний. '
                                                                 'Набагато зросла трудова активність колгоспників, які '
                                                                 'все наочніше переконуються у невигідності витрачати '
                                                                 'час на роботу у власному городі і більше працюють у '
                                                                 'громадському господарстві (Колг. Укр., 10, 1960, 9); '
                                                                 'До середини XIX ст. цілком виявилась економічна '
                                                                 'невигідність підневільної кріпацької праці (Іст. '
                                                                 'СРСР, II, 1957, 203).',
                                                   'sovietization_risk': 1,
                                                   'keywords': ['колгоспник', 'колективізація'],
                                                   'historical_note': 'Радянський словник СУМ-11 ілюструє поняття '
                                                                      'ідеологізованим прикладом про роботу в '
                                                                      'колгоспах.'},
                   'pre_soviet_witness': None},
                  {'headword': 'невигі́дність',
                   'short_label': 'збитковість, фінансова або практична невигода',
                   'gloss': 'unprofitability, economic disadvantage or unfavourableness',
                   'pos': 'noun',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[nɛwɪˈɦʲidnʲisʲtʲ]'},
                   'stress': {'form': 'невигі́дність',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/невигідність'},
                   'morphology': {'pos': 'іменник',
                                  'paradigm': {'kind': 'noun',
                                               'gender': 'жіночий',
                                               'animacy': 'inanimate',
                                               'cases': {'називний': {'singular': 'невигі́дність'},
                                                         'родовий': {'singular': 'невигі́дності'},
                                                         'давальний': {'singular': 'невигі́дності'},
                                                         'знахідний': {'singular': 'невигі́дність'},
                                                         'орудний': {'singular': 'невигі́дністю'},
                                                         'місцевий': {'singular': 'невигі́дності'},
                                                         'кличний': {'singular': 'невигі́дносте'}}}},
                   'distinction_note': 'Позначає економічну або практичну невигоду, збитковість угоди чи справи (від '
                                       'невигі́дний — безприбутковий). Не плутати з побутовою незручністю '
                                       '«неви́гідність».',
                   'meaning': {'definitions': ['Властивість за значенням невигі́дний (який не дає прибутку, '
                                               'збитковий).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НЕВИГІ́ДНІСТЬ, ності, ж., розм. Абстр. ім. до '
                                                                 'невигі́дний.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None}],
 'нівідки': [{'headword': 'ні́відки',
              'short_label': 'нема звідки взяти, відсутність джерела (діал.)',
              'gloss': 'nowhere to get or obtain from, absence of source (dialectal)',
              'pos': 'adv',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈɲiwidkɪ]'},
              'stress': {'form': 'ні́відки', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/нівідки'},
              'morphology': {'pos': 'прислівник'},
              'distinction_note': 'Діалектний прислівник: означає відсутність джерела, звідки можна щось узяти чи '
                                  'дістати (те саме, що ні́відкіля / ні́звідки; наголос на першому складі). Не плутати '
                                  'з «ніві́дки» (ні з якого місця).',
              'meaning': {'definitions': ['Немає звідки взяти, дістати; те саме, що ні́відкіля (діал.).'],
                          'source': 'ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'НІ́ВІДКИ, присл., діал. Ні́відкіля. — Посилаймо депутацію '
                                                            'до цісаря!.. Вияснім йому, що нам нівідки платити таку '
                                                            'суму! — почулися голоси мужиків (Фр., VIII, 1952, 23).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': None},
             {'headword': 'ніві́дки',
              'short_label': 'ні з якого місця, нізвідки (діал., літ.)',
              'gloss': 'from no place, from nowhere, out of nowhere (dialectal/literary)',
              'pos': 'adv',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ɲiˈwidkɪ]'},
              'stress': {'form': 'ніві́дки', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/нівідки'},
              'morphology': {'pos': 'прислівник'},
              'distinction_note': 'Діалектний та класичний літературний прислівник місця: ні з якого місця, нізвідки '
                                  '(те саме, що нівідкіля́ / нізві́дки; наголос на другому складі, як у Панаса '
                                  'Мирного). Не плутати з «ні́відки» (нема звідки взяти).',
              'meaning': {'definitions': ['Ні з якого місця, ні з якого боку; те саме, що нівідкіля́ (діал., літ.).'],
                          'source': 'ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'НІВІ́ДКИ, присл., діал. Нівідкіля́. Він довго ходив. Усе '
                                                            'кругом спало мертвим сном, нівідки не доходило ніякого '
                                                            'гуку (Мирний, III, 1954, 374).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': None}],
 'обрость': [{'headword': 'о́брость',
              'short_label': 'обростання водяними організмами предметів у воді (спец.)',
              'gloss': 'biofouling, encrustation by aquatic organisms on submerged structures',
              'pos': 'noun',
              'cefr': 'C1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈɔbrɔsʲtʲ]'},
              'stress': {'form': 'о́брость', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/обрость'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'жіночий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'о́брость', 'plural': 'о́брості'},
                                                    'родовий': {'singular': 'о́брості', 'plural': 'о́бростей'},
                                                    'давальний': {'singular': 'о́брості', 'plural': 'о́бростям'},
                                                    'знахідний': {'singular': 'о́брость', 'plural': 'о́брості'},
                                                    'орудний': {'singular': 'о́бростю', 'plural': 'о́бростями'},
                                                    'місцевий': {'singular': 'о́брості', 'plural': 'о́бростях'},
                                                    'кличний': {'singular': 'о́бросте', 'plural': 'о́брості'}}}},
              'distinction_note': 'Спеціальний гідробіологічний термін: шар молюсків чи водоростей, що осідають на дні '
                                  'суден чи гідроспоруд (біообростання). Не плутати з рослинно-родовим «обро́сть» '
                                  '(молоді пагони, молодь).',
              'meaning': {'definitions': ['Поселення водяних організмів на поверхні предметів, що перебувають у воді '
                                          '(спец.).'],
                          'source': 'ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'О́БРОСТЬ, і, ж., спец. Поселення водяних організмів на '
                                                            'предметах, спорудах, що стикаються з водою.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': None},
             {'headword': 'обро́сть',
              'short_label': 'молоді пагони рослини; перен. нове покоління, молодь (збірн.)',
              'gloss': 'young shoots, green growth; figuratively young offspring or generation',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ɔˈbrɔsʲtʲ]'},
              'stress': {'form': 'обро́сть',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/обрость'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'жіночий',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'обро́сть', 'plural': 'обро́сті'},
                                                    'родовий': {'singular': 'обро́сті', 'plural': 'обро́стей'},
                                                    'давальний': {'singular': 'обро́сті', 'plural': 'обро́стям'},
                                                    'знахідний': {'singular': 'обро́сть', 'plural': 'обро́сті'},
                                                    'орудний': {'singular': 'обро́стю', 'plural': 'обро́стями'},
                                                    'місцевий': {'singular': 'обро́сті', 'plural': 'обро́стях'},
                                                    'кличний': {'singular': 'обро́сте', 'plural': 'обро́сті'}}}},
              'distinction_note': 'Народне слово: молоді пагони дерев, зелена порість; переносно — молодь, діти («У '
                                  'нашого роду обрості мало»). Не плутати з гідробіологічним «о́брость» (обростання '
                                  'під водою).',
              'meaning': {'definitions': ['Молоді стебла або пагони дерева; перен. молодь, нове покоління (збірне, '
                                          'рідко).'],
                          'source': 'Грінченко (1907) / ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'ОБРО́СТЬ, і, ж., збірн., рідко. 1. розм. Молоді стебла '
                                                            'рослини; пагони. Обрость на дереві (Сл. Гр.). 2. перен. '
                                                            'Молодь, нове покоління.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Обрость, -ти, ж. Побеги. Обрость на дереві. Кролев. у. У нашого роду '
                                              'обрости мало, рід щось не плодовитий. Г. Барв. 275.',
                                     'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                        'Грінченком в умовах дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                        'р.).'}}],
 'перекочування': [{'headword': 'переко́чування',
                    'short_label': 'дія за значенням перекочувати (переміщення коченням)',
                    'gloss': 'rolling over, shifting by rolling or tumbling across (action)',
                    'pos': 'noun',
                    'cefr': 'B2',
                    'heritage_status': {'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                    'pronunciation': {'ipa': '[pɛrɛˈkɔt͡ʃʊwɐnʲːɐ]'},
                    'stress': {'form': 'переко́чування',
                               'source': 'ВТС',
                               'url': 'https://slovnyk.me/dict/vts/перекочування'},
                    'morphology': {'pos': 'іменник',
                                   'paradigm': {'kind': 'noun',
                                                'gender': 'середній',
                                                'animacy': 'inanimate',
                                                'cases': {'називний': {'singular': 'переко́чування',
                                                                       'plural': 'переко́чування'},
                                                          'родовий': {'singular': 'переко́чування',
                                                                      'plural': 'переко́чувань'},
                                                          'давальний': {'singular': 'переко́чуванню',
                                                                        'plural': 'переко́чуванням'},
                                                          'знахідний': {'singular': 'переко́чування',
                                                                        'plural': 'переко́чування'},
                                                          'орудний': {'singular': 'переко́чуванням',
                                                                      'plural': 'переко́чуваннями'},
                                                          'місцевий': {'singular': 'переко́чуванні',
                                                                       'plural': 'переко́чуваннях'},
                                                          'кличний': {'singular': 'переко́чування',
                                                                      'plural': 'переко́чування'}}}},
                    'distinction_note': 'Означає переміщення предметів (бочки, колоди) чи рослин коченням з одного '
                                        'місця на інше (від переко́чувати). Не плутати з «перекочува́ння» '
                                        '(переселення, перекочовування).',
                    'meaning': {'definitions': ['Дія за значенням переко́чувати (переміщення коченням з одного місця '
                                                'на інше).'],
                                'source': 'ВТС'},
                    'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ПЕРЕКО́ЧУВАННЯ, я, с. Дія за знач. переко́чувати і '
                                                                  'перекочува́тися. При перекочуванні рослин по полю '
                                                                  'насіння з них випадає і розсівається (Бур’яни.., '
                                                                  '1957, 16); Перекочування обруча.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                       'Наведено для лексикографічної прозорості.'},
                    'pre_soviet_witness': None},
                   {'headword': 'перекочува́ння',
                    'short_label': 'переселення, зміна місця перебування (перекочовування)',
                    'gloss': 'relocation, seasonal migration, nomadic moving from place to place (action)',
                    'pos': 'noun',
                    'cefr': 'B2',
                    'heritage_status': {'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                    'pronunciation': {'ipa': '[pɛrɛkɔt͡ʃʊˈwɑnʲːɐ]'},
                    'stress': {'form': 'перекочува́ння',
                               'source': 'ВТС',
                               'url': 'https://slovnyk.me/dict/vts/перекочування'},
                    'morphology': {'pos': 'іменник',
                                   'paradigm': {'kind': 'noun',
                                                'gender': 'середній',
                                                'animacy': 'inanimate',
                                                'cases': {'називний': {'singular': 'перекочува́ння',
                                                                       'plural': 'перекочува́ння'},
                                                          'родовий': {'singular': 'перекочува́ння',
                                                                      'plural': 'перекочува́нь'},
                                                          'давальний': {'singular': 'перекочува́нню',
                                                                        'plural': 'перекочува́нням'},
                                                          'знахідний': {'singular': 'перекочува́ння',
                                                                        'plural': 'перекочува́ння'},
                                                          'орудний': {'singular': 'перекочува́нням',
                                                                      'plural': 'перекочува́ннями'},
                                                          'місцевий': {'singular': 'перекочува́нні',
                                                                       'plural': 'перекочува́ннях'},
                                                          'кличний': {'singular': 'перекочува́ння',
                                                                      'plural': 'перекочува́ння'}}}},
                    'distinction_note': 'Означає переселення, зміну місця перебування чи пасовища разом з майном і '
                                        'худобою (дія за значенням перекочува́ти = перекочо́вувати). Не плутати з '
                                        'коченням предметів «переко́чування».',
                    'meaning': {'definitions': ['Дія за значенням перекочува́ти (перекочо́вувати — переселення, '
                                                'перехід на інше місце).'],
                                'source': 'ВТС'},
                    'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ПЕРЕКОЧУВА́ННЯ, я, с. Дія за знач. перекочува́ти.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                       'Наведено для лексикографічної прозорості.'},
                    'pre_soviet_witness': None}],
 'переплавний': [{'headword': 'перепла́вний',
                  'short_label': 'у словосполученні «перепла́вна середа» (Преполовення)',
                  'gloss': 'pertaining to Mid-Pentecost (folk/ecclesiastical spring festival)',
                  'pos': 'adj',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[pɛrɛˈpɫɑwnɪj]'},
                  'stress': {'form': 'перепла́вний',
                             'source': 'Грінченко (1907) / ВТС',
                             'url': 'https://slovnyk.me/dict/vts/переплавний'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Етнографічний та церковний вислів: «перепла́вна середа́» — середина між '
                                      'Великоднем і Трійцею (Преполовення). Не плутати з виробничим «переплавни́й» '
                                      '(одержаний переплавленням).',
                  'meaning': {'definitions': ['У народній назві «перепла́вна середа́» (весняне свято Преполовення, '
                                              'середина між Великоднем і Трійцею).'],
                              'source': 'Грінченко (1907) / ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПЕРЕПЛА́ВНИЙ, а, е: ◊ Перепла́вна середа́ — '
                                                                'православне весняне свято, що припадало на середину '
                                                                'між паскою і трійцею. В переплавну середу '
                                                                'перепливають.. річку, щоб судорога не змикала ноги, '
                                                                'як плаватиме (Номис, 1864, № 456); Довго стояла вода '
                                                                'весняна, пам’ятаю. Ще в переплавну середу було її '
                                                                'багато по левадах і долинах (Довж., Зач. Десна, 1957, '
                                                                '488).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                         'quote': 'Переплавний, -а, -е. Переплавна середа. Преполовеніе. У переплавну '
                                                  'середу пасла дівка череду. Н. п.',
                                         'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                            'Грінченком в умовах дії антиукраїнських імперських указів '
                                                            '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                            'р.).'}},
                 {'headword': 'переплавни́й',
                  'short_label': 'одержаний шляхом переплавлення металу чи сировини',
                  'gloss': 'remelted, smelted or obtained by melting down',
                  'pos': 'adj',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[pɛrɛpɫɐwˈnɪj]'},
                  'stress': {'form': 'переплавни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/переплавний'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Металургійний та виробничий термін: прикметник від «перепла́вити» (переплавний '
                                      'метал, переплавна смола чи віск). Не плутати зі святом «перепла́вна середа».',
                  'meaning': {'definitions': ['Отриманий або оброблений шляхом переплавлення (про метал, віск і '
                                              'под.).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПЕРЕПЛАВНИ́Й, а́, е́. Отриманий шляхом переплавлення.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'переповзати': [{'headword': 'перепо́взати',
                  'short_label': 'побувати скрізь поповзом (про багатьох, док.)',
                  'gloss': 'crawl all over, visit many places by crawling (perf., distributive)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[pɛrɛˈpɔwzɐtɪ]'},
                  'stress': {'form': 'перепо́взати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/переповзати'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': "Означає дію багатьох суб'єктів: повзаючи, побувати в усіх чи багатьох місцях "
                                      '(доконаний вид: переповзали всі кутки). Не плутати з недоконаним «переповза́ти» '
                                      '(переповзати через перешкоду).',
                  'meaning': {'definitions': ['Повзаючи, побувати в усіх або багатьох місцях (доконаний вид).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПЕРЕПО́ВЗАТИ, аю, аєш, док., розм. Повзаючи, побувати '
                                                                'в усіх або багатьох місцях.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'переповза́ти',
                  'short_label': 'переміщатися поповзом через щось або з місця на місце (недок.)',
                  'gloss': 'crawl across, creep over an obstacle or crawl from place to place (imperf.)',
                  'pos': 'verb',
                  'cefr': 'A2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[pɛrɛpɔwˈzɑtɪ]'},
                  'stress': {'form': 'переповза́ти',
                             'source': 'Грінченко (1907) / ВТС',
                             'url': 'https://slovnyk.me/dict/vts/переповзати'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Основне значення руху: повзти через перешкоду, дорогу, перелаз або повільно '
                                      'пересуватися (недок. вид до переповзти). Не плутати з доконаним «перепо́взати» '
                                      '(побувати всюди поповзом).',
                  'meaning': {'definitions': ['Поповзом переміщатися через що-небудь або з місця на місце (недоконаний '
                                              'вид до переповзти).'],
                              'source': 'Грінченко (1907) / ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПЕРЕПОВЗА́ТИ, а́ю, а́єш, недок., ПЕРЕПОВЗТИ́, зу́, '
                                                                'зе́ш, док. 1. перех., через що. Поповзом переміщатися '
                                                                'через кого-, що-небудь, на іншу сторону чогось. '
                                                                'Фелікс і Воля з дівчинкою переповзли Прорізну вулицю '
                                                                'й готувалися пірнути в каналізаційний люк, коли знову '
                                                                'почули собачий гавкіт (Ю. Янов., II, 1954, 43); // '
                                                                'розм. Перебиратися через що-небудь повільно, з '
                                                                'труднощами. З’явилися перші замети, через які автобус '
                                                                'переповзав з величезним зусиллям (Донч., VI, 1957, '
                                                                '539); — Мале воно [хлоп’я] ще, мале, — жалісно '
                                                                'прикладає жінка руку до щоки. — Так за день '
                                                                'натомиться, навихається, що через перелаз не може '
                                                                'переповзти (Стельмах, І, 1962, 454). 2. неперех. '
                                                                'Плазуючи, переміщатися по якомусь просторі. Козакову '
                                                                'доводилось посуватися з своєю групою повільно, весь '
                                                                'час маскуючись, місцями переповзаючи '
                                                                'по-пластунському, бо з кряжу.. часто обзивалися '
                                                                'ворожі кулемети (Гончар, III, 1959, 105); До своїх '
                                                                'людей Захарові в цю мить уже не можна було '
                                                                'переповзати по мосту, як це зробив він уночі (Ле, '
                                                                'Право.., 1957, 121); // Плазуючи, перебиратися з '
                                                                'одного місця на інше. Курсанти зриваються з місця, '
                                                                'біжать вперед, падають, переповзають на 3-4 кроки '
                                                                'вбік від того місця, де впали, знову схоплюються на '
                                                                'ноги, мчать до висоти (Багмут, Служу Рад. Союзу, '
                                                                '1950, 79); Вони [розвідники] переповзли за кам’яний '
                                                                'виступ, ближче до містка (Кучер, Чорноморці, 1956, '
                                                                '308); Мухіддінов переповз на правий бік плоту і '
                                                                'обережно взяв весло (Голов., Тополя.., 1965, 387); // '
                                                                'Не маючи ніг, пересуватися по поверхні всім тулубом '
                                                                '(про плазунів). Я на прикорні присів, мов сонний, І '
                                                                'дивився тупо і без сил. Аж змія переповзла нарешті… '
                                                                '(Крим., Вибр., 1965, 39); // перен., ірон. Переходити '
                                                                'в наступний клас з низькими оцінками. Увесь клас і '
                                                                'директор добре знали, як вчилася Параска, ледве на '
                                                                'трійки витягувала, переповзала з класу в клас (Цюпа, '
                                                                'Вічний вогонь, 1960, 23); // перен. Пересуватися (про '
                                                                'промінь, відблиск світил і т. ін.). Небо на сході '
                                                                'зовсім поблякло і тьмяний відблиск його поволі '
                                                                'переповзав на захід (Голов., Тополя.., 1965, 220); '
                                                                'Місячний промінь повз по долівці, дійшов до голови '
                                                                'Малуші.., переповз ще трохи й зупинився на постолах '
                                                                '(Скл., Святослав, 1959, 82).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                         'quote': 'Переповзати, -зАю, -єш, сов. в. переповзтИ, -зУ, -зЕш, гл. '
                                                  'Переползать, переползти.',
                                         'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                            'Грінченком в умовах дії антиукраїнських імперських указів '
                                                            '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                            'р.).'}}],
 'перетіпати': [{'headword': 'переті́пати',
                 'short_label': 'закінчити тіпати або потрясти багатьох (про пропасницю, док.)',
                 'gloss': 'shake or convulse thoroughly (of fever/chills, perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛrɛˈtʲipɐtɪ]'},
                 'stress': {'form': 'переті́пати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/перетіпати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Медично-побутове значення: про пропасницю чи лихоманку — закінчити тіпати або '
                                     'потрясти багатьох хворих (доконаний вид). Не плутати з «перетіпа́ти» (витіпати '
                                     'льон наново).',
                 'meaning': {'definitions': ['Закінчити тіпати або потрясти багатьох (про лихоманку чи пропасницю; '
                                             'доконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕТІ́ПАТИ, ає, док. 1. Закінчити тіпати (про '
                                                               'пропасницю). 2. Потіпати всіх або багатьох (про '
                                                               'пропасницю).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'перетіпа́ти',
                 'short_label': 'потіпати весь льон чи коноплі або повторно їх витіпати (док.)',
                 'gloss': 'scutch/shake all flax or re-scutch hemp fibers (perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɛrɛtʲiˈpɑtɪ]'},
                 'stress': {'form': 'перетіпа́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/перетіпати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Сільськогосподарське значення: обробити тріпанням весь урожай льону чи конопель, '
                                     'або протіпати волокно вдруге/наново (доконаний вид). Не плутати з «переті́пати» '
                                     '(про лихоманку).',
                 'meaning': {'definitions': ['Потіпати весь льон чи коноплі або витіпати волокно заново/повторно '
                                             '(доконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПЕРЕТІПА́ТИ, а́ю, а́єш, док., перех. 1. Потіпати все '
                                                               'або багато чого-небудь (про льон, коноплю і т. ін.). '
                                                               '2. Тіпати льон, коноплю і т. ін. ще раз, повторно або '
                                                               'заново, по-іншому.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'пікірування': [{'headword': 'пікі́рування',
                  'short_label': 'стрімкий політ літака майже вертикально вниз (авіа)',
                  'gloss': 'nose-dive, diving of an aircraft at high speed',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[piˈkirʊwɐnʲːɐ]'},
                  'stress': {'form': 'пікі́рування', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пікірування'},
                  'morphology': {'pos': 'іменник',
                                 'paradigm': {'kind': 'noun',
                                              'gender': 'середній',
                                              'animacy': 'inanimate',
                                              'cases': {'називний': {'singular': 'пікі́рування',
                                                                     'plural': 'пікі́рування'},
                                                        'родовий': {'singular': 'пікі́рування',
                                                                    'plural': 'пікі́рувань'},
                                                        'давальний': {'singular': 'пікі́руванню',
                                                                      'plural': 'пікі́руванням'},
                                                        'знахідний': {'singular': 'пікі́рування',
                                                                      'plural': 'пікі́рування'},
                                                        'орудний': {'singular': 'пікі́руванням',
                                                                    'plural': 'пікі́руваннями'},
                                                        'місцевий': {'singular': 'пікі́руванні',
                                                                     'plural': 'пікі́руваннях'},
                                                        'кличний': {'singular': 'пікі́рування',
                                                                    'plural': 'пікі́рування'}}}},
                  'distinction_note': 'Авіаційний термін: дія за значенням «пікі́рувати» (стрімкий крутий спуск літака '
                                      'вниз по похилій траєкторії). Не плутати з агрономічним «пікірува́ння» '
                                      '(пересаджування розсади).',
                  'meaning': {'definitions': ['Стрімкий рух літака майже вертикально вниз по похилій траєкторії '
                                              '(авіація).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПІКІ́РУВАННЯ, я, с. Дія за знач. пікі́рувати.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'пікірува́ння',
                  'short_label': 'пересаджування молодих сіянців рослин за допомогою піки (агро)',
                  'gloss': 'pricking out, transplanting young seedlings using a dibber (horticulture)',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[pikirʊˈwɑnʲːɐ]'},
                  'stress': {'form': 'пікірува́ння', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пікірування'},
                  'morphology': {'pos': 'іменник',
                                 'paradigm': {'kind': 'noun',
                                              'gender': 'середній',
                                              'animacy': 'inanimate',
                                              'cases': {'називний': {'singular': 'пікірува́ння',
                                                                     'plural': 'пікірува́ння'},
                                                        'родовий': {'singular': 'пікірува́ння',
                                                                    'plural': 'пікірува́нь'},
                                                        'давальний': {'singular': 'пікірува́нню',
                                                                      'plural': 'пікірува́нням'},
                                                        'знахідний': {'singular': 'пікірува́ння',
                                                                      'plural': 'пікірува́ння'},
                                                        'орудний': {'singular': 'пікірува́нням',
                                                                    'plural': 'пікірува́ннями'},
                                                        'місцевий': {'singular': 'пікірува́нні',
                                                                     'plural': 'пікірува́ннях'},
                                                        'кличний': {'singular': 'пікірува́ння',
                                                                    'plural': 'пікірува́ння'}}}},
                  'distinction_note': 'Агрономічний термін: дія за значенням «пікірува́ти» (пересаджування розсади та '
                                      'сіянців у парники чи ґрунт із підрізанням кореня). Не плутати з авіаційним '
                                      '«пікі́рування» (політ донизу).',
                  'meaning': {'definitions': ['Пересаджування молодих рослин або сіянців з укороченням кореня для '
                                              'розсаджування (садівництво, агрономія).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПІКІРУВА́ННЯ, я, с. Дія за знач. пікірува́ти. '
                                                                'Вирощувати сіянці для пікірування краще у парниках '
                                                                '(Озелен. колг. села, 1955, 104).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'пікірувати': [{'headword': 'пікі́рувати',
                 'short_label': 'стрімко ринути майже вертикально вниз (про літак)',
                 'gloss': 'dive steeply, nose-dive in an airplane',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[piˈkirʊwɐtɪ]'},
                 'stress': {'form': 'пікі́рувати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пікірувати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Авіаційний термін: на великій швидкості круто спускатися вниз по похилій '
                                     'траєкторії (про літак). Не плутати з рослинницьким «пікірува́ти» (пересаджувати '
                                     'розсаду).',
                 'meaning': {'definitions': ['На великій швидкості стрімко знижуватися майже вертикально вниз (про '
                                             'літальний апарат).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПІКІ́РУВАТИ, ую, уєш, недок. 1. док. На великій '
                                                               'швидкості ринутися майже вертикально вниз (про літак). '
                                                               '— Насмілюсь доповісти, що це, здається, той самий '
                                                               'радянський літак, який перебив мені подорож на фронт… '
                                                               'Він пікірує! (Ю. Янов., І, 1954, 152); Літаки зробили '
                                                               'коло, але замість того, щоб іти на посадку, почали '
                                                               'пікірувати на аеродром (Мушк., Чорний хліб, 1960, 17); '
                                                               '// Стрімко летіти вниз (звичайно про птахів). Час від '
                                                               'часу.. то одна, то друга пташина каменем пікірувала '
                                                               'донизу (Збан., Мор. чайка, 1959, 22).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'пікірува́ти',
                 'short_label': 'пересаджувати сіянці рослин із підрізанням головного кореня (агро)',
                 'gloss': 'prick out, transplant seedlings with root pinching',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pikirʊˈwɑtɪ]'},
                 'stress': {'form': 'пікірува́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пікірувати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Агрономічний термін: пересаджувати молоді сіянці за допомогою спеціального '
                                     'кілочка (піки) з прищипуванням кореня. Не плутати з авіаційним «пікі́рувати» '
                                     '(круто знижуватися в польоті).',
                 'meaning': {'definitions': ['Пересаджувати молоді рослини (сіянці) з відщипуванням кінчика кореня за '
                                             'допомогою кілочка.'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПІКІРУВА́ТИ, у́ю, у́єш, недок. і док., перех. '
                                                               'Пересаджувати рослину в молодому віці за допомогою '
                                                               'кілочка — піки. Пікірують розсаду при появі першого '
                                                               'справжнього листка в торфоперегнійні або гончарні '
                                                               'горщечки (Овоч. закр. і відкр. грунту, 1957, 54); — '
                                                               'Коли сходи зарунились, тисячу найбільш кущистих із них '
                                                               'я обережно пікірувала і пересадила на грядку, як '
                                                               'розсаду (Донч., V, 1957, 239).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'пікіруватися': [{'headword': 'пікі́руватися',
                   'short_label': 'обмінюватися шпильками, колкими або ущипливими словами',
                   'gloss': 'bicker, spar verbally, exchange sharp barbs',
                   'pos': 'verb',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[piˈkirʊwɐtɪsʲɐ]'},
                   'stress': {'form': 'пікі́руватися',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/пікіруватися'},
                   'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                   'distinction_note': 'Означає перекидатися ущипливими, саркастичними репліками або гострими слівцями '
                                       'в суперечці. Не плутати з «пікірува́тися» (бути розсаджуваним про сіянці).',
                   'meaning': {'definitions': ['Обмінюватися шпильками, гострими чи ущипливими словами у розмові '
                                               '(недоконаний вид).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ПІКІ́РУВАТИСЯ, уюся, уєшся, недок., з ким. '
                                                                 'Обмінюватись ущипливими словами. Мсьє і мадам Енно, '
                                                                 'пікіруючися гострими слівцями з приводу щойно '
                                                                 'пережитих пригод, стояли поруч на носі катера '
                                                                 '(Смолич, Світанок.., 1953, 43).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None},
                  {'headword': 'пікірува́тися',
                   'short_label': 'бути пересадженим (пасивний стан до пікірувати рослини)',
                   'gloss': 'be pricked out or transplanted (passive of horticulture action)',
                   'pos': 'verb',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[pikirʊˈwɑtɪsʲɐ]'},
                   'stress': {'form': 'пікірува́тися',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/пікіруватися'},
                   'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                   'distinction_note': 'Пасивний стан до агрономічного дієслова «пікірува́ти» (про розсаду, яку '
                                       'проріджують і пересаджують). Не плутати зі словесною дуеллю «пікі́руватися» '
                                       '(обмін шпильками).',
                   'meaning': {'definitions': ['Пасивний стан до пікірува́ти (про сіянці та саджанці рослин).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ПІКІРУВА́ТИСЯ, у́ється, недок. Пас. до пікірува́ти.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None}],
 'побережник': [{'headword': 'побере́жник',
                 'short_label': 'невеликий перелітний навколоводний птах (кулик-побережник)',
                 'gloss': 'sandpiper, small migratory shorebird (genus Calidris)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔbɛˈrɛʒnɪk]'},
                 'stress': {'form': 'побере́жник', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/побережник'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'чоловічий',
                                             'animacy': 'animate',
                                             'cases': {'називний': {'singular': 'побере́жник',
                                                                    'plural': 'побере́жники'},
                                                       'родовий': {'singular': 'побере́жника',
                                                                   'plural': 'побере́жників'},
                                                       'давальний': {'singular': 'побере́жникові / побере́жнику',
                                                                     'plural': 'побере́жникам'},
                                                       'знахідний': {'singular': 'побере́жника',
                                                                     'plural': 'побере́жників'},
                                                       'орудний': {'singular': 'побере́жником',
                                                                   'plural': 'побере́жниками'},
                                                       'місцевий': {'singular': 'побере́жникові / побере́жнику',
                                                                    'plural': 'побере́жниках'},
                                                       'кличний': {'singular': 'побере́жнику',
                                                                   'plural': 'побере́жники'}}}},
                 'distinction_note': 'Орнітологічний термін: невеликий кулик роду Calidris, що гніздиться в тундрі та '
                                     'зупиняється на річкових косах. Не плутати з професією сторожа «побережни́к» '
                                     '(лісовий/береговий доглядач).',
                 'meaning': {'definitions': ['Невеликий перелітний птах ряду сивкоподібних, що тримається морських і '
                                             'річкових берегів (рід Calidris).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОБЕРЕ́ЖНИК, а, ч. (Саlidris). Невеликий перелітний '
                                                               'птах.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'побережни́к',
                 'short_label': 'прибережний лісник, береговий сторож, наглядач (заст.)',
                 'gloss': 'coastal guard, riparian warden or forest ranger along waterways',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔbɛrɛʒˈnɪk]'},
                 'stress': {'form': 'побережни́к',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/побережник'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'чоловічий',
                                             'animacy': 'animate',
                                             'cases': {'називний': {'singular': 'побережни́к',
                                                                    'plural': 'побережники́'},
                                                       'родовий': {'singular': 'побережника́',
                                                                   'plural': 'побережникі́в'},
                                                       'давальний': {'singular': 'побережникові́ / побережнику́',
                                                                     'plural': 'побережника́м'},
                                                       'знахідний': {'singular': 'побережника́',
                                                                     'plural': 'побережникі́в'},
                                                       'орудний': {'singular': 'побережнико́м',
                                                                   'plural': 'побережника́ми'},
                                                       'місцевий': {'singular': 'побережникові́ / побережнику́',
                                                                    'plural': 'побережника́х'},
                                                       'кличний': {'singular': 'побережнику́',
                                                                   'plural': 'побережники́'}}}},
                 'distinction_note': 'Історична назва професії: лісовий або прирічковий сторож, полесовщик, доглядач '
                                     'берегів та панських угідь. Не плутати з птахом «побере́жник» (кулик).',
                 'meaning': {'definitions': ['Лісовий або прибережний сторож, полесовщик (заст.).'],
                             'source': 'Грінченко (1907) / ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОБЕРЕЖНИ́К, а́, ч., заст. Лісовий сторож. Там далі.. '
                                                               'лежав.. «сусідський» ліс. Чужий, невеликий і лиш рідко '
                                                               'побережниками звідуваний (Коб., II, 1956, 67); '
                                                               'Численні стада худоби на полонинах, гриби і ягоди в '
                                                               'лісі, риба у воді — все було не твоє, не людське, а '
                                                               'панське, якого день і ніч пильнували озброєні поліцаї, '
                                                               'побережники (Козл., Сонце.., 1957, 4).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Побережник, -ка, м. Лесной страж, полесовщик, лесник. Kolb. І. 68. '
                                                 'Уман. у. Хотин. у.',
                                        'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                           'Грінченком в умовах дії антиукраїнських імперських указів '
                                                           '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                           'р.).'}}],
 'повищати': [{'headword': 'пови́щати',
               'short_label': 'стати вищим на зріст або піднятися вгору (док.)',
               'gloss': 'grow taller, increase in height or stature (perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈwɪʃt͡ʃɐtɪ]'},
               'stress': {'form': 'пови́щати',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/повищати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «стати вищим, підрости, виструнчитися (доконаний вид: повищав, повищала)». '
                                   'Не плутати з «повища́ти» (провищати, пови верещати якийсь час).',
               'meaning': {'definitions': ['Зробитися вищим на зріст або за положенням; піднятися вгору (доконаний '
                                           'вид).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОВИ́ЩАТИ, аю, аєш. Док. до ви́щати. Сині очі в дівчини '
                                                             'знов освітили обличчя, і постать немов повищала (Л. '
                                                             'Укр., III, 1952, 581); Храпков аж повищав, молодецьки '
                                                             'обернувся й побіг (Ле, Міжгір’я, 1953, 35).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Повищати, -щаю, -єш, гл. Сделаться выше.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}},
              {'headword': 'повища́ти',
               'short_label': 'провищати якийсь час, пови верещати (док.)',
               'gloss': 'squeal, shriek or screech for a while (perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔwɪˈʃt͡ʃɑtɪ]'},
               'stress': {'form': 'повища́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/повищати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає видавати пронизливий крик, верещати або вищати протягом певного часу '
                                   '(доконаний вид: повищу́, повища́ть). Не плутати з «пови́щати» (стати вищим на '
                                   'зріст).',
               'meaning': {'definitions': ['Вищати, верещати або пронизливо кричати якийсь час (доконаний вид).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОВИЩА́ТИ, щу́, щи́ш, док. Вища́ти якийсь час.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'пожалити': [{'headword': 'пожа́лити',
               'short_label': 'пожаліти, змилосердитися над кимось (діал., нар.)',
               'gloss': 'take pity on, show mercy to, feel sorry for (dialectal/folk, perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈʒɑlɪtɪ]'},
               'stress': {'form': 'пожа́лити', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пожалити'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Народнопоетичне та діалектне дієслово: пожаліти, змилуватися над кимось («Пожаль '
                                   'мене, милий Боже!»). Не плутати з «пожали́ти» (ужалити бджолою чи кропивою).',
               'meaning': {'definitions': ['Пожаліти, виявити жалість або співчуття (діал., народнопоетичне; доконаний '
                                           'вид).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЖА́ЛИТИ, лю, лиш, док., перех., діал. Пожаліти. Пожаль '
                                                             'мене, милий боже, що я молоденька (Чуб., V, 1874, 831).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'пожали́ти',
               'short_label': 'покусати жалом або обпекти кропивою (док.)',
               'gloss': 'sting severely with nettles or bees (perf.)',
               'pos': 'verb',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔʒɐˈlɪtɪ]'},
               'stress': {'form': 'пожали́ти',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/пожалити'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає «вжалити когось, покусати жалом або обпекти кропивою (доконаний вид до '
                                   'жалити)». Не плутати з народним «пожа́лити» (пожаліти, змилуватися).',
               'meaning': {'definitions': ['Ужалити або обпекти кропивою чи жалом (доконаний вид до жалити).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЖАЛИ́ТИ, жалю́, жа́лиш, док., перех. 1. Док. до '
                                                             'жали́ти. Якби на кропиву не мороз, вона б усіх людей '
                                                             'пожалила (Укр.. присл.., 1955, 220); Прийшла [Параска] '
                                                             'до їх близенько та й упала в гущавину, аж вуха пожалила '
                                                             'собі кропивою (Н.-Лев., II, 1956, 15); У лісі трохи '
                                                             'подряпався [Клим], пожалив і руки, крізь кущі '
                                                             'пробираючись (Грим., Кавалер.., 1955, 293); Я не '
                                                             'скаржуся ніколи, Як мене пожалять бджоли (Стельмах, Живі '
                                                             'огні, 1954, 72). 2. Жалити якийсь час.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Пожалити, -лю, -лИш, гл. Пожалить, изжалить. Як би на кропиву не '
                                               'мороз, вона б всіх людей пожалила. Ном. № 3825.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}}],
 'пожалитися': [{'headword': 'пожа́литися',
                 'short_label': 'змилосердитися, пожаліти себе чи когось (діал.)',
                 'gloss': 'take pity on oneself or someone, feel compassion (dialectal, perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔˈʒɑlɪtɪsʲɐ]'},
                 'stress': {'form': 'пожа́литися',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/пожалитися'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Діалектне та фольклорне значення: пожаліти когось або поскаржитися на долю («Ой '
                                     'пожалься, милий Боже, дівчиноньки»). Не плутати з «пожали́тися» (обпекти себе '
                                     'кропивою чи жалом).',
                 'meaning': {'definitions': ['Пожаліти або змилосердитися (діал., народне; доконаний вид).'],
                             'source': 'Грінченко (1907) / ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОЖА́ЛИТИСЯ, люся, лишся, док., діал. 1. Пожаліти. '
                                                               'Такі романи писати, то краще пір’я дерти. А пожалься '
                                                               'боже того пера й чорнила! (Л. Укр., V, 1956, 64); — У '
                                                               'вас голос… — Пожалься боже, який там голос… (Добр., '
                                                               'Очак. розмир, 1965, 38). 2. Пожалітися. А знов, як не '
                                                               'вгодять Галі брати, то Галя поплаче й погорює, '
                                                               '..пожалиться та й годі (Вовчок, І, 1955, 288).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Пожалитися, -люся, -лишся, гл. 1) Сжалиться над кем; пожалеть кого. '
                                                 'Ой пожалься, милий Боже, дівчиноньки молодої. Мет. 260. 2) Пожалеть '
                                                 'чего. Пожалься, Боже, собаці білого хліба. Ном. № 10780.',
                                        'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                           'Грінченком в умовах дії антиукраїнських імперських указів '
                                                           '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                           'р.).'}},
                {'headword': 'пожали́тися',
                 'short_label': 'ужалитися, обпектися кропивою чи жалом (док.)',
                 'gloss': 'sting oneself with nettles or insects (perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔʒɐˈlɪtɪsʲɐ]'},
                 'stress': {'form': 'пожали́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пожалитися'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Означає обпекти себе кропивою або випадково ужалити себе колючкою чи жалом '
                                     '(доконаний вид зворотний). Не плутати зі співчутливим «пожа́литися» (пожаліти, '
                                     'змилосердитися).',
                 'meaning': {'definitions': ['Ужалити себе або потерпіти від уколу жалом чи кропивою (доконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОЖАЛИ́ТИСЯ, жалю́ся, жа́лишся, док. 1. Пожалити себе. '
                                                               '2. Жалитися якийсь час.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'пожарище': [{'headword': 'пожа́рище',
               'short_label': "величезна пожежа, полум'яне згарище (збільш.)",
               'gloss': 'huge fire, raging blaze or roaring conflagration (augmentative)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈʒɑrɪʃt͡ʃɛ]'},
               'stress': {'form': 'пожа́рище', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пожарище'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'середній',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'пожа́рище', 'plural': 'пожа́рища'},
                                                     'родовий': {'singular': 'пожа́рища', 'plural': 'пожа́рищ'},
                                                     'давальний': {'singular': 'пожа́рищу', 'plural': 'пожа́рищам'},
                                                     'знахідний': {'singular': 'пожа́рище', 'plural': 'пожа́рища'},
                                                     'орудний': {'singular': 'пожа́рищем', 'plural': 'пожа́рищами'},
                                                     'місцевий': {'singular': 'пожа́рищі', 'plural': 'пожа́рищах'},
                                                     'кличний': {'singular': 'пожа́рище', 'plural': 'пожа́рища'}}}},
               'distinction_note': "Збільшувальне до слова «пожар»: величезне полум'я, масштабна нищівна пожежа (як у "
                                   'Шевченка: «Поки люди з поля пожарище не пустили»). Не плутати з місцем вигорілої '
                                   'хати «пожари́ще» (згарище).',
               'meaning': {'definitions': ['Збільшувальне до пожар: велика, нищівна пожежа.'], 'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЖА́РИЩЕ, а, с. Збільш. до пожа́р; велика пожежа. Довго '
                                                             'воно [село] зеленіло, Поки люди з поля Пожарище не '
                                                             'пустили Та не запалили Села того зеленого. Згоріло, '
                                                             'зотліло (Шевч., II, 1963, 172); В очі йому вдарило '
                                                             'сліпуче пожарище, нестерпне вогняне сяйво (Ю. Бедзик, '
                                                             'Полки.., 1959, 26).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'пожари́ще',
               'short_label': 'місце, де була пожежа; згарище',
               'gloss': 'site of a fire, burned-down area, charred ruins',
               'pos': 'noun',
               'cefr': 'B1',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔʒɐˈrɪʃt͡ʃɛ]'},
               'stress': {'form': 'пожари́ще',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/пожарище'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'середній',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'пожари́ще', 'plural': 'пожари́ща'},
                                                     'родовий': {'singular': 'пожари́ща', 'plural': 'пожари́щ'},
                                                     'давальний': {'singular': 'пожари́щу', 'plural': 'пожари́щам'},
                                                     'знахідний': {'singular': 'пожари́ще', 'plural': 'пожари́ща'},
                                                     'орудний': {'singular': 'пожари́щем', 'plural': 'пожари́щами'},
                                                     'місцевий': {'singular': 'пожари́щі', 'plural': 'пожари́щах'},
                                                     'кличний': {'singular': 'пожари́ще', 'plural': 'пожари́ща'}}}},
               'distinction_note': 'Означає залишки після пожежі, згарище, випалене вогнем місце («на пожарищі лишився '
                                   "лиш попіл»). Не плутати із самим полум'ям «пожа́рище» (велика пожежа).",
               'meaning': {'definitions': ['Місце, де сталася пожежа; залишки згорілої будівлі чи поселення '
                                           '(згарище).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЖАРИ́ЩЕ, а, с. Місце, де була пожежа; те, що лишилось '
                                                             'після пожежі. В холодну ніч самотній мандрівець в глухім '
                                                             'бору знайшов старе кострище: при місяці білів холодний '
                                                             'попілець, чорніло вколо нього пожарище (Л. Укр., І, '
                                                             '1951, 282); Серед київських пожарищ і руїн.. важко було '
                                                             'розшукати знайомий будинок (Жур., Вел. розмова, 1955, '
                                                             '97); *Образно. — Хіба довго можна так жити? Це ж не '
                                                             'життя, а якесь пожарище (Шиян, Баланда, 1957, 145).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Пожарище, -ща, с. = пожарина. Полилися ріки крови, пожар погасили, а '
                                               'німчики пожарище й сиріт поділили. Шевч. 237.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}}],
 'позбігати': [{'headword': 'позбі́гати',
                'short_label': 'швидко оббігати всюди або побувати в багатьох місцях (док.)',
                'gloss': 'run around everywhere, visit many places on foot rapidly (perf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[pɔzˈbiɦɐtɪ]'},
                'stress': {'form': 'позбі́гати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/позбігати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає швидко обійти, оббігати якусь територію чи багатьох сусідів («позбігати '
                                    'стежечки, оббігати всіх подруг»; док. вид). Не плутати з «позбіга́ти» (зійтися '
                                    'звідусіль або стекти докупи).',
                'meaning': {'definitions': ['Швидко обходити або оббігати якусь територію, побувати скрізь (доконаний '
                                            'вид).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОЗБІ́ГАТИ, аю, аєш, док., перех., розм. Швидко '
                                                              'обходи́ти, оббі́гати якусь територію, побувати скрізь '
                                                              'або в багатьох місцях. Там-то стежечок і до води й до '
                                                              'сусіди, і до другої. Все то позбігали, повиходжували '
                                                              'легесенькі ніжечки дівочі (Вовчок, І, 1955, 181).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'позбіга́ти',
                'short_label': 'стекти донизу, зійтися або зібратися докупи (про багатьох, док.)',
                'gloss': 'run down, drain off (liquids) or gather together in crowds (perf.)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[pɔzbiˈɦɑtɪ]'},
                'stress': {'form': 'позбіга́ти',
                           'source': 'Грінченко (1907) / ВТС',
                           'url': 'https://slovnyk.me/dict/vts/позбігати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає збігтися разом багатьом людям чи тваринам, або стекти воді після танення '
                                    'снігу («позбігалися води, позбігали люди»; док. вид). Не плутати з дією оббігання '
                                    '«позбі́гати».',
                'meaning': {'definitions': ['Стекти донизу або зібратися звідусіль разом (про багатьох людей або '
                                            'рідину; доконаний вид).'],
                            'source': 'Грінченко (1907) / ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОЗБІГА́ТИ, а́є, а́ємо, а́єте, док. 1. Стекти скрізь '
                                                              'або в багатьох місцях (про рідину). Порозтавали сніги, '
                                                              'зійшла повідь, позбігала скрізь вода (Кв.-Осн., II, '
                                                              '1956, 122); // тільки мн., розм. Втратити частину '
                                                              'вмісту рідини, яка виливається через край при закипанні '
                                                              '(про все або багато чогось). Семениха.. прикладає до '
                                                              'ватри трісок і пантрує, аби горшки не позбігали '
                                                              '(Черемш., Тв., 1960, 88). 2. тільки мн. Збігти '
                                                              'куди-небудь (про всіх або багатьох). З двора й собаки '
                                                              'наші позбігали (Сл. Гр.).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'Позбігати, -гаємо, -єте, гл. Сбежать (о многих). З двора й собаки '
                                                'наші позбігали. Г. Барв. 54.',
                                       'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                          'Грінченком в умовах дії антиукраїнських імперських указів '
                                                          '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                          'р.).'}}],
 'позорювати': [{'headword': 'позо́рювати',
                 'short_label': 'зорати все або багато ділянок землі (док.)',
                 'gloss': 'plough up entirely, till multiple fields (perf., distributive)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔˈzɔrʲʊwɐtɪ]'},
                 'stress': {'form': 'позо́рювати',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/позорювати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Сільськогосподарське значення: зорати все поле або багато ділянок землі у '
                                     'багатьох місцях (доконаний вид від орати). Не плутати з «позорюва́ти» (ночувати '
                                     'просто неба чи спати на світанку).',
                 'meaning': {'definitions': ['Зорати все або багато чого-небудь у багатьох місцях (доконаний вид).'],
                             'source': 'Грінченко (1907) / ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОЗО́РЮВАТИ, юю, юєш, док., перех. Зорати все або '
                                                               'багато чого-небудь, скрізь або в багатьох місцях.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Позорювати, -рюю, -єш, гл. Вспахать (во множестве).',
                                        'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                           'Грінченком в умовах дії антиукраїнських імперських указів '
                                                           '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                           'р.).'}},
                {'headword': 'позорюва́ти',
                 'short_label': 'ночувати просто неба, спати на світанку якийсь час (док.)',
                 'gloss': 'spend the night outdoors, sleep at dawn, or stay awake through the night for a while '
                          '(perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔzɔrʲʊˈwɑtɪ]'},
                 'stress': {'form': 'позорюва́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/позорювати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Означає ночувати просто неба, спати на світанку або не спати вночі якийсь час '
                                     '(доконаний вид від зорюва́ти). Не плутати з оранням землі «позо́рювати».',
                 'meaning': {'definitions': ['Зорювати (ночувати просто неба, спати на світанку або не спати вночі) '
                                             'якийсь час (доконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОЗОРЮВА́ТИ, ю́ю, ю́єш, док. Зорювати якийсь час. '
                                                               'Певне, їм [бійцям] теж хотілося хоч трохи поніжитися, '
                                                               'позорювати, але не можна — була команда… (Руд., Вітер… '
                                                               '1958, 88); — А тепер, сину, скачи на хутір і чекай там '
                                                               'моїх наказів. Вранці, думаю, почнеться.. Скачи, Марку. '
                                                               'До світанку позорюй ще… (Рибак, Дніпро, 1953, 278).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'покрапати': [{'headword': 'покра́пати',
                'short_label': 'покрапати якийсь час (про невеликий дощ, док.)',
                'gloss': 'drizzle or sprinkle lightly for a while (of rain, perf.)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[pɔˈkrɑpɐtɪ]'},
                'stress': {'form': 'покра́пати',
                           'source': 'Грінченко (1907) / ВТС',
                           'url': 'https://slovnyk.me/dict/vts/покрапати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає невеликий дощ, що крапав обмежений час (доконаний вид: «покрапає та й '
                                    'перестане»). Не плутати з тривалим періодичним процесом «покрапа́ти» (капотіти '
                                    'час від часу).',
                'meaning': {'definitions': ['Крапати якийсь час (про дощ або рідину; доконаний вид).'],
                            'source': 'Грінченко (1907) / ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОКРА́ПАТИ, покра́паю, покра́паєш і покра́плю, '
                                                              'покра́плеш, док. 1. неперех. Крапати якийсь час (про '
                                                              'дощ). — Літо зійде — дощ не покрапає (Гончар, Тронка, '
                                                              '1963, 61). 2. перех. Вкрити щось краплями чого-небудь. '
                                                              'Як гарно ложку ніс [батько] до рота, підтримуючи знизу '
                                                              'шкоринкою хліба, щоб не покрапать рядно (Довж., Зач. '
                                                              'Десна, 1957, 478). 3. перех., перен. Вкрити якусь '
                                                              'поверхню чим-небудь дрібним у багатьох місцях. — Збудую '
                                                              '[хату], уже й майстрів договорив, обсаджу тополями й '
                                                              'вишнями. Старенькій матері звелю покрапати навколо '
                                                              'запашними квітками (Головко, І, 1957, 69).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'Покрапати, -паю, -єш, гл. Покапать.',
                                       'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                          'Грінченком в умовах дії антиукраїнських імперських указів '
                                                          '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                          'р.).'}},
               {'headword': 'покрапа́ти',
                'short_label': 'крапати потроху або час від часу (недок.)',
                'gloss': 'drip occasionally, trickle in small drops intermittently (imperf.)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[pɔkrɐˈpɑtɪ]'},
                'stress': {'form': 'покрапа́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/покрапати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': 'Означає періодичне або тривале падіння крапель з перервами («дощ покрапає…»; '
                                    'недоконаний вид). Не плутати з доконаним «покра́пати» (покрапати якийсь час і '
                                    'припинитися).',
                'meaning': {'definitions': ['Крапати потроху або час від часу (про дрібний дощ; недоконаний вид).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОКРАПА́ТИ, а́є, недок. Крапати потроху або час від '
                                                              'часу (про дощ). Ніч… темно… дощ покрапає… (Хотк., '
                                                              'Довбуш, 1965, 301).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'полик': [{'headword': 'по́лик',
            'short_label': "зменшувальне до піл (дерев'яний поміст для спання)",
            'gloss': 'small wooden sleeping bench or berth (diminutive of піл)',
            'pos': 'noun',
            'cefr': 'B2',
            'heritage_status': {'classification': 'standard',
                                'is_russianism': False,
                                'russian_shadow': False,
                                'vesum_attested': True},
            'pronunciation': {'ipa': '[ˈpɔlɪk]'},
            'stress': {'form': 'по́лик',
                       'source': 'Грінченко (1907) / ВТС',
                       'url': 'https://slovnyk.me/dict/vts/полик'},
            'morphology': {'pos': 'іменник',
                           'paradigm': {'kind': 'noun',
                                        'gender': 'чоловічий',
                                        'animacy': 'inanimate',
                                        'cases': {'називний': {'singular': 'по́лик', 'plural': 'по́лики'},
                                                  'родовий': {'singular': 'по́лика', 'plural': 'по́ликів'},
                                                  'давальний': {'singular': 'по́ликові / по́лику',
                                                                'plural': 'по́ликам'},
                                                  'знахідний': {'singular': 'по́лик', 'plural': 'по́лики'},
                                                  'орудний': {'singular': 'по́ликом', 'plural': 'по́ликами'},
                                                  'місцевий': {'singular': 'по́ликові / по́лику', 'plural': 'по́ликах'},
                                                  'кличний': {'singular': 'по́лику', 'plural': 'по́лики'}}}},
            'distinction_note': 'Зменшувальне до «піл»: поміст із дощок біля печі в традиційній хаті, на якому сплять. '
                                'Не плутати з деталю одягу «поли́к» (плечова вставка сорочки).',
            'meaning': {'definitions': ["Зменшувальне до піл: дерев'яний поміст для спання в традиційній українській "
                                        'хаті.'],
                        'source': 'Грінченко (1907) / ВТС'},
            'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                            'definition': 'ПО́ЛИК, а, ч. Зменш. до піл. Біля полика, на якому він '
                                                          'лежав, сиділа незнайома чорнява молодиця (Баш, Проф. Буйко, '
                                                          '1946, 18); На полику спить старший син Сандер (Шиян, '
                                                          'Переможці, 1950, 6).',
                                            'sovietization_risk': 0,
                                            'keywords': [],
                                            'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено для '
                                                               'лексикографічної прозорості.'},
            'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                   'quote': 'Полик, -ка, ж. Ум. от піл.',
                                   'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом Грінченком '
                                                      'в умовах дії антиукраїнських імперських указів (Валуєвського '
                                                      'циркуляра 1863 р. та Емського указу 1876 р.).'}},
           {'headword': 'поли́к',
            'short_label': 'вставка, верхня частина рукава традиційної сорочки (етн.)',
            'gloss': 'shoulder insert or embroidered gusset of traditional Ukrainian shirt',
            'pos': 'noun',
            'cefr': 'B2',
            'heritage_status': {'classification': 'standard',
                                'is_russianism': False,
                                'russian_shadow': False,
                                'vesum_attested': True},
            'pronunciation': {'ipa': '[pɔˈlɪk]'},
            'stress': {'form': 'поли́к', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/полик'},
            'morphology': {'pos': 'іменник',
                           'paradigm': {'kind': 'noun',
                                        'gender': 'чоловічий',
                                        'animacy': 'inanimate',
                                        'cases': {'називний': {'singular': 'поли́к', 'plural': 'полики́'},
                                                  'родовий': {'singular': 'полика́', 'plural': 'поликі́в'},
                                                  'давальний': {'singular': 'поликові́ / полику́',
                                                                'plural': 'полика́м'},
                                                  'знахідний': {'singular': 'поли́к', 'plural': 'полики́'},
                                                  'орудний': {'singular': 'полико́м', 'plural': 'полика́ми'},
                                                  'місцевий': {'singular': 'поликові́ / полику́', 'plural': 'полика́х'},
                                                  'кличний': {'singular': 'полику́', 'plural': 'полики́'}}}},
            'distinction_note': 'Етнографічний термін народного строю: вишита плечова вставка жіночої чи чоловічої '
                                "сорочки, що з'єднує стан із рукавом. Не плутати зі спальним помостом «по́лик».",
            'meaning': {'definitions': ['Прямокутна або трапецієподібна вставка у верхній частині рукава традиційної '
                                        'української сорочки.'],
                        'source': 'ВТС'},
            'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                            'definition': 'ПОЛИ́К, а́, ч., діал. Верхня частина рукава сорочки. В '
                                                          'жіночій сорочці вишивали полики, підопліччя, чохли, поділ '
                                                          '(Нар. тв. та етн., 1, 1966, 55); [Оксана:] Поки паламар '
                                                          'збереться ударити в дзвін, то я й полика дошию (Кроп., І, '
                                                          '1958, 123); За день Христина встигла стовкти мак і збити '
                                                          'олію, роздерти на жорнах миску.. гречки і вишити зо дві '
                                                          'квітки на поликах (Стельмах, І, 1962, 156); // Поперечна '
                                                          'вишивка на верхній частині рукава сорочки, на кінцях '
                                                          'рушника і т. ін. Вишивка на жіночих сорочках '
                                                          'розташовувалась на рукавах двома рядами. Верхній ряд — '
                                                          'полик — мав ширину 10-15 см (Нар. тв. та етн., 1, 1963, '
                                                          '87); І писанок, і крашанок, Всього Трохиму надавала '
                                                          '[дівчина]. Із поликами рушничок В зелені свята обіцяла '
                                                          '(Рудан., Тв., 1959, 63).',
                                            'sovietization_risk': 0,
                                            'keywords': [],
                                            'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено для '
                                                               'лексикографічної прозорості.'},
            'pre_soviet_witness': None}],
 'половник': [{'headword': 'поло́вник',
               'short_label': 'засік, приміщення або повітка для зберігання полови',
               'gloss': 'chaff bin, granary section or barn for chaff storage',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈɫɔwnɪk]'},
               'stress': {'form': 'поло́вник',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/половник'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'чоловічий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'поло́вник', 'plural': 'поло́вники'},
                                                     'родовий': {'singular': 'поло́вника', 'plural': 'поло́вників'},
                                                     'давальний': {'singular': 'поло́вникові / поло́внику',
                                                                   'plural': 'поло́вникам'},
                                                     'знахідний': {'singular': 'поло́вник', 'plural': 'поло́вники'},
                                                     'орудний': {'singular': 'поло́вником', 'plural': 'поло́вниками'},
                                                     'місцевий': {'singular': 'поло́вникові / поло́внику',
                                                                  'plural': 'поло́вниках'},
                                                     'кличний': {'singular': 'поло́внику', 'plural': 'поло́вники'}}}},
               'distinction_note': 'Сільськогосподарська споруда: спеціальний засік або хлів у клуні для зсипання '
                                   'полови після молотьби. Не плутати з історичним станом селянина «половни́к» '
                                   '(орендар за половину врожаю).',
               'meaning': {'definitions': ['Місце чи засік у клуні, куди зсипають полову після молотьби.'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЛО́ВНИК, а, ч. Місце, куди зсипають полову; засік для '
                                                             'полови. Треба було повитрясати приколотки, поскладати їх '
                                                             'на купу, попідмітати вимолочене зерно, повиносити трину '
                                                             'до половника (Фр., III, 1950, 271); Забув ти, як спав '
                                                             'бувало по багацьких половниках і обходив панську худобу? '
                                                             '(Ірчан, II, 1958, 134).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Половник, -ка, м. 1) Закром для мякины. Угор. 2) Род хлева для мякины '
                                               'и пр. — иногда как часть клуни, иногда отдельно. Чуб. VII. 397. Лохв. '
                                               'у. Славяносерб. у. В Галиціи хлев, где зимой стоит овцы и телята. Фр. '
                                               'Пр. 136.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}},
              {'headword': 'половни́к',
               'short_label': 'феодально залежний селянин, що віддавав половину врожаю (іст.)',
               'gloss': 'feudal sharecropper peasant paying half the harvest to the lord (hist.)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔɫɔwˈnɪk]'},
               'stress': {'form': 'половни́к', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/половник'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'чоловічий',
                                           'animacy': 'animate',
                                           'cases': {'називний': {'singular': 'половни́к', 'plural': 'половники́'},
                                                     'родовий': {'singular': 'половника́', 'plural': 'половникі́в'},
                                                     'давальний': {'singular': 'половникові́ / половнику́',
                                                                   'plural': 'половника́м'},
                                                     'знахідний': {'singular': 'половника́', 'plural': 'половникі́в'},
                                                     'орудний': {'singular': 'половнико́м', 'plural': 'половника́ми'},
                                                     'місцевий': {'singular': 'половникові́ / половнику́',
                                                                  'plural': 'половника́х'},
                                                     'кличний': {'singular': 'половнику́', 'plural': 'половники́'}}}},
               'distinction_note': 'Історичний термін соціального устрою: селянин-дольщик, який орендував землю '
                                   'землевласника під виплату половини врожаю (половинини). Не плутати із засіком для '
                                   'полови «поло́вник».',
               'meaning': {'definitions': ['Феодально залежний селянин у давній Україні, який орендував землю, '
                                           'віддаючи половину врожаю (іст.).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЛОВНИ́К, а́, ч., іст. Феодально залежний селянин, який '
                                                             'працював на землі феодала, віддаючи йому половину '
                                                             'врожаю. Селяни повинні були віддавати боярам значну '
                                                             'частину врожаю (близько половини — через що вони '
                                                             'називалися половниками) (Іст. СРСР, І, 1956, 65).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'полупати': [{'headword': 'полу́пати',
               'short_label': 'поморгати, покліпати очима якийсь час (док., розм.)',
               'gloss': "blink or flutter one's eyes for a while (colloquial, perf.)",
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈɫupɐtɪ]'},
               'stress': {'form': 'полу́пати',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/полупати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає кліпати чи моргати очима деякий час («полупати очима»; доконаний вид від '
                                   'лу́пати). Не плутати з колонням дров «полупа́ти» (поколоти поліна).',
               'meaning': {'definitions': ['Лупати (кліпати, моргати) очима якийсь час (доконаний вид).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЛУ́ПАТИ, аю, аєш, док., фам. Лупати якийсь час. Івась, '
                                                             'полупавши очима і поскрібши у потилиці, знову ліг і '
                                                             'зразу заснув (Мирний, IV, 1955, 22).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Полупати, -паю, -єш, гл. — очима. Похлопать, поморгать глазами. Офіцер '
                                               'полупав-полупав очима, за шапку та й за двері. О. 1861. IX. 77.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}},
              {'headword': 'полупа́ти',
               'short_label': 'порубати, поколоти на поліна дрова чи колоду (док., діал.)',
               'gloss': 'chop, split or cleave firewood/logs (dialectal, perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔɫuˈpɑtɪ]'},
               'stress': {'form': 'полупа́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/полупати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Діалектне значення: розколоти або розрубати колоду на поліна чи дрова (доконаний '
                                   'вид від лупа́ти — колоти). Не плутати з морганням очима «полу́пати».',
               'meaning': {'definitions': ['Поколоти або порубати на шматки дрова чи колоду (діал.; доконаний вид).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОЛУПА́ТИ, а́ю, а́єш, док., перех., діал. Поколоти, '
                                                             'порубати. [Юлія:] Я тобі принесу зараз одну колодку, та '
                                                             'полупай, коли вже так наперся! (Фр., IX, 1952, 154).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'помикати': [{'headword': 'поми́кати',
               'short_label': 'розчесати і підготувати пучки льону або конопель (док.)',
               'gloss': 'comb out and prepare flax/hemp bundles (mychky) for spinning (perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈmɪkɐtɪ]'},
               'stress': {'form': 'поми́кати',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/помикати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': "Традиційне ремесло: підготувати та розчесати прядиво, зв'язавши його в мички перед "
                                   'прядінням (доконаний вид). Не плутати з деспотичним командуванням «помика́ти» '
                                   '(попихати кимось).',
               'meaning': {'definitions': ["Розчесати льон або коноплі, пов'язавши в мички для прядіння (доконаний "
                                           'вид).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОМИ́КАТИ, поми́каю, поми́каєш і поми́чу, поми́чеш, '
                                                             'док., перех. 1. Розчесати льон або коноплі, пов’язавши в '
                                                             'мички і приготувавши для прядіння. На́ тобі круг '
                                                             'прядива: щоб ти його пом’яла, потіпала і в мички '
                                                             'помикала (Сл. Гр.). 2. Ми́кати якийсь час.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Помикати, -каю, -єш, гл. Расчесать и приготовить для пряденія пеньку '
                                               "или лен. Мил. М. 16. На тобі круг прядіва: щоб ти його пом'яла, "
                                               'потіпала і в мички поткала. Рудч. Ск. II. 44.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}},
              {'headword': 'помика́ти',
               'short_label': 'деспотично командувати, попихати кимось (недок.)',
               'gloss': 'boss around, push around or domineer over someone (imperf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔmɪˈkɑtɪ]'},
               'stress': {'form': 'помика́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/помикати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': 'Означає свавільно або зневажливо керувати людьми, змушувати виконувати забаганки, '
                                   'попихати («будуть мною помикати»; недоконаний вид). Не плутати з підготовкою льону '
                                   '«поми́кати».',
               'meaning': {'definitions': ['Деспотично розпоряджатися ким-небудь; попихати (недоконаний вид).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОМИКА́ТИ, а́ю, а́єш, недок. 1. неперех. Деспотично '
                                                             'розпоряджатися ким-небудь; попихати. Будуть мною '
                                                             'помикати, Стануть з мене глузувати (Метл. і Кост., Тв., '
                                                             '1906, 53); [Сохвія Станиславівна:] Чи довго ще будуть '
                                                             'помикать нами гнобителі? Хто ж захистить.. од '
                                                             'кровопивців?! (Кроп., IV, 1959, 218). 2. перех., перен., '
                                                             'розм. Приваблювати до себе; // безос. Не видно моєї '
                                                             'хати, тільки видно грушу, Туди ж мою помикає щовечора '
                                                             'душу (Чуб., V, 1874, 61). 3. неперех., перен., розм. '
                                                             'Дуже швидко пересуватися; поспішати. Вертаєшся, було, то '
                                                             'наче ззаду чорт доганяє, — так помикаєш (Свидн., '
                                                             'Люборацькі, 1955, 24); // чим. Вправно діяти. Ой поїхав '
                                                             'мій миленький у ліс по деревце, Утне мені куделечку, '
                                                             'любе моє серце. Утне мені куделечку з сіма [сьома] '
                                                             'зубочками, Буду прясти, помикати білими ручками '
                                                             '(Коломийки, 1969, 21).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'попадатися': [{'headword': 'попа́датися',
                 'short_label': 'розлізтися, роздертися, зноситися від довгого носіння (діал., док.)',
                 'gloss': 'wear out, fray, disintegrate from long wear (dialectal, perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔˈpɑdɐtɪsʲɐ]'},
                 'stress': {'form': 'попа́датися',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/попадатися'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Діалектне та народне значення: зноситися, розлізтися, порватися від тривалого '
                                     'носіння («Носив сорочку, поки попадалась»; доконаний вид). Не плутати з '
                                     'недоконаним «попада́тися» (потрапляти в пастку чи на очі).',
                 'meaning': {'definitions': ['Розлізтися, потертися або зноситися від довгого вжитку (діал., доконаний '
                                             'вид; зафіксовано Грінченком).'],
                             'source': 'Грінченко (1907) / ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОПА́ДАТИСЯ, ається, док., діал. 1. Розлізтися. Носив '
                                                               'сорочку, поки попадалась (Сл. Гр.); — Я зараз надіну '
                                                               '[сорочку й штани]. Моє попадалось, дак оце, спасибі '
                                                               'вам, тепер зніму, виперу да й полатаю (Барв., Опов.., '
                                                               '1902, 29). 2. Зморщившись, обвиснути. Шкура попадалась '
                                                               'на шиї (Сл. Гр.).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Попадатися 1, -даюся, -єшся, гл. Распасться, опасть. Шкура '
                                                 'попадалась на шиї. Носив сорочку, поки попадалась. Зараз надіну. Моє '
                                                 'попадалось, дак оце, спасибі вам, тепер зніму. Г. Барв. 29.',
                                        'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                           'Грінченком в умовах дії антиукраїнських імперських указів '
                                                           '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                           'р.).'}},
                {'headword': 'попада́тися',
                 'short_label': 'траплятися на очі, потрапляти в пастку або сітку (недок.)',
                 'gloss': 'get caught, fall into a trap, chance upon or come across (imperf.)',
                 'pos': 'verb',
                 'cefr': 'A2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔpɐˈdɑtɪsʲɐ]'},
                 'stress': {'form': 'попада́тися',
                            'source': 'Грінченко (1907) / ВТС',
                            'url': 'https://slovnyk.me/dict/vts/попадатися'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Загальновживане дієслово: бути схопленим, спійманим у пастку, або випадково '
                                     "з'являтися перед очима («попадатися під гарячу руку»; недоконаний вид). Не "
                                     'плутати зі зношуванням одягу «попа́датися».',
                 'meaning': {'definitions': ['Потрапляти в пастку, сітку, або випадково траплятися комусь на очі '
                                             '(недоконаний вид до попастися).'],
                             'source': 'Грінченко (1907) / ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПОПАДА́ТИСЯ, а́юся, а́єшся, недок., ПОПА́СТИСЯ, '
                                                               'аду́ся, аде́шся, док. 1. кому і без додатка. Бути '
                                                               'схопленим, упійманим ким-небудь. Повстанці виділили їм '
                                                               'старий рибальський баркас на веслах і, побажавши '
                                                               'вдруге не попадатись, з миром відпустили в море, до '
                                                               'своїх (Гончар, II, 1959, 53); Їхала вона Чорним гаєм і '
                                                               'попалася розбійникам (Вовчок, І, 1955, 358); Хтось '
                                                               'підходить іззаду і з криком хапає за плечі: «Ага! '
                                                               'Попалася!» (Хотк., II, 1966, 217); // Бути спійманим у '
                                                               'пастку, сіті і т. ін. (про тварин). Якось попалася '
                                                               'Лисичка — Злодюга, вовчика сестричка, — Хвостом в '
                                                               'капкан (Мирний, V, 1955, 381); На цей раз попався '
                                                               'довгий і гладкий в’юн (Стельмах, На.. землі, 1949, '
                                                               '326); *Образно. Я тобі на вірність клявся, До '
                                                               'серденька пригортав, В сіті власні я попався І за '
                                                               'правду жарт прийняв (Л. Укр., IV, 1954, 106); // Бути '
                                                               'впійманим на якому-небудь вчинку, викритим у чомусь. '
                                                               'Дибляни набігли [на коноводів], махаючи кийками й '
                                                               'ломаками та гукаючи: — А, бісові шкуродери, '
                                                               'попалися!.. (Гр., II, 1963, 296); [Ольга:] У тресті — '
                                                               'не нахваляться ним — незамінимий чоловік, а тут… Душу '
                                                               'за гроші продасть і не попадеться (Зар., Антеї, 1962, '
                                                               '264); // у що і без додатка. Опинятися в несприятливих '
                                                               'обставинах, скрутному становищі. — Сидів би вже, коли '
                                                               'попався. Ну, два роки дали б йому (Головко, II, 1957, '
                                                               '47); — Ти, молодице, вільності шукаєш? — А вона: — Я. '
                                                               '— Попадешся, у біду, дурна! Лучче служи своїй панії та '
                                                               'роби (Вовчок, І, 1955, 262). ◊ Попа́стися на ву́дочку '
                                                               '— те саме, що Попа́стися (спійма́тися і т. ін.) на '
                                                               'ву́дку ( див. ву́дка); Попада́тися (попа́стися) в '
                                                               'лабе́ти див. лабе́ти; Попада́тися (попа́стися) на '
                                                               'гачо́к див. гачо́к; Попада́тися (попа́стися) у ла́пи '
                                                               'див. ла́па. 2. між кого, кому, в що. Опинятися в '
                                                               'якому-небудь місці, в якомусь оточенні, у когось. Живе '
                                                               'на острові цариця, Цирцея, люта чарівниця і дуже злая '
                                                               'до людей; Які лиш не остережуться, А їй на острів '
                                                               'попадуться, Тих переверне на звірей [звірів] (Котл., '
                                                               'І, 1952, 159); А то ж і не страшно, скажете, щоб '
                                                               'живому чоловікові та попастись меж мерців? (Кв.-Осн., '
                                                               'II, 1956, 107); — О співець, як ти попався У '
                                                               'відьомськую хатину? За що так немилосердно Ти '
                                                               'обернутий в собаку? (Л. Укр., IV, 1954, 184); // '
                                                               'Оселятися, влаштовуватися працювати де-небудь, у '
                                                               'когось. Голос оповідав звичайну історію втікачів: «і '
                                                               'попавсь я до грека, і зазнав я неволі ще гіршої, як '
                                                               'вдома» (Коцюб., І, 1955, 345); // Ставати належним до '
                                                               'складу якого-небудь суспільного об’єднання, '
                                                               'організації і т. ін. Він попався нам у бригаду; // '
                                                               'кому, рідко до кого і без додатка. Потрапляти в '
                                                               'чиє-небудь розпорядження, опинятися в якихось '
                                                               'стосунках з ким-небудь. — Скільки я знав горбатих, усе '
                                                               'їм такі кралі попадаються, що ну! (Гончар, III, 1959, '
                                                               '200); Вона ж між ними [паничами], мов тая перепеличка, '
                                                               'звивається. — Котрий-то з них попадеться? — говоримо, '
                                                               'було, дівчата… — Дознає неборак, почім ківш лиха! '
                                                               '(Вовчок, І, 1955, 111); // Ставати об’єктом уваги в '
                                                               'пресі, кіно і т. ін. Вкінці він оженився, став '
                                                               'адвокатом і патріотом, календар «Просвіти» помістив '
                                                               'його портрет, потім попався в «Альбум заслужених '
                                                               'Русинів» (Мак., Вибр., 1954, 3). ◊ Попада́тися '
                                                               '(попа́стися) на язи́к (на язика́) кому— стати об’єктом '
                                                               'розмов. Жінкам тільки попадися на язика, засічуть, мов '
                                                               'ті оси! (Горд., II, 1959, 248); Попа́стися на зу́бки '
                                                               '(на зубо́к) кому — те саме, що Потра́пити (попа́сти) '
                                                               'на [го́стрі (голо́дні)] зу́би кому ( див. зуб). '
                                                               '[Іван:] Він же мені попадеться на зубок: я йому '
                                                               'допечу, коли не кулаком, то язиком (Кроп., І, 1958, '
                                                               '65). 3. Зустрічатися на шляху; траплятися. Вона '
                                                               'починала ходити та проходжати по луці, зривала квіти, '
                                                               'що попадалися, з опалом впивала їх пахощі (Вовчок, І, '
                                                               '1955, 320); На тротуарах впадало в очі — серед '
                                                               'вирядженої публіки безліч офіцерні, просто військових, '
                                                               'напіввійськових.. І навіть попадались (це бачили '
                                                               'вперше славгородці) — зовсім в оперетковому вбранні '
                                                               '(Головко, II, 1957, 430); І йшла [Маруся] відтак '
                                                               'додому тим самим меланхолійним кроком; лагідним рухом '
                                                               'пестила корову, що попалася по дорозі (Хотк., II, '
                                                               '1966, 43); // Знаходитися, з’являтися при виконанні '
                                                               'якоїсь дії. — Ждемо, що ви що-небудь відкриєте, '
                                                               'розгадаєте якусь тайну.. — Їм більше глиняні черепочки '
                                                               'попадаються (Гончар, Тронка, 1963, 273); Піт солоний '
                                                               'пролива [перекладач зі стажем]. — Ну й попалися слова! '
                                                               'Аж розпухла голова (Ющ., Люди.., 1959, 234); // '
                                                               'Випадково траплятися в якихось обставинах. Я стараюсь '
                                                               'читати більше путніх книжок, хоч їх тут і трудно '
                                                               'достать і більш попадається дурних книжок, ніж '
                                                               'розумних (Л. Укр., V, 1956, 10); Горе було, як '
                                                               'попадався чужосторонній чоловік і не пізнавав в '
                                                               'старчукові пушкарського отамана (Хотк., II, 1966, '
                                                               '115); // тільки недок. З’являтися в певному місці. '
                                                               'Сиза імла рідшала, димочок де-не-де вже звивався, вже '
                                                               'люди попадались і коло криниці (Вовчок, І, 1955, 295); '
                                                               '// у сполуч. з прикм. Трапившись, виявлятись '
                                                               'яким-небудь. Любив [пан] .. баб різками бити. '
                                                               'Захльобувався від радості, коли баба попадалася '
                                                               'вересклива (Хотк., II, 1966, 116); — А по чому ж там, '
                                                               'Іване, Дурні продаються? — Та то, пане, як до дурня: '
                                                               'Які попадуться! (Руд., Тв., 1956, 113); — Прислали '
                                                               'комісара. Ми хотіли без нього обійтись, але, коли '
                                                               'послухали, — залишили при собі. Підходящий чоловік '
                                                               'попався (Стельмах, II, 1962, 86); Тріснув кілок із '
                                                               'тину. Давид зупинився й оглянувся. Видно, кілок '
                                                               'трухлявий попався (Головко, II, 1957, 91). Не '
                                                               'попада́йся (не попада́йтеся) мені́ — уживається як '
                                                               'погроза у знач. не зустрічайся (не зустрічайтеся) '
                                                               'мені. — Не попадайся ж і ти мені, білоголова крисо! '
                                                               '(Мирний, IV, 1955, 98); [Микита:] Ой бесуре, не '
                                                               'попадайся ти мені! (Кроп., І, 1958, 64). ◊ Попада́тися '
                                                               '(попа́стися) на о́чі див. о́ко¹; Попада́тися '
                                                               '(попа́стися) під ру́ку (ру́ки) див. рука́. 4. тільки '
                                                               'док. Дістатися кому-небудь. — Таке добро, а, дивись, '
                                                               'наймичці попалось, — з якимось жалем подумав Салоган '
                                                               'про дівочу вроду (Стельмах, І, 1962, 346); Нам '
                                                               'попалися звичайні «телячі» вагони, подовбані за війну '
                                                               'кулями та осколками (Гончар, III, 1959, 341). ♦ '
                                                               'Попада́тися (попа́стися) до рук (у ру́ки) див. рука́.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                        'quote': 'Попадатися 2, -даюся, -єшся, сов. в. попастися, -дУся, -дЕшся, гл. '
                                                 'Попадаться, попасться, быть пойману, захвачену. Попалася в лихі руки '
                                                 'невірній дружині. Мет. 253.',
                                        'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                           'Грінченком в умовах дії антиукраїнських імперських указів '
                                                           '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                           'р.).'}}]}
