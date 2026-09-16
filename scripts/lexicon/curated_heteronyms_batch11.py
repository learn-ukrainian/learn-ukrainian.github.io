"""Curated heteronym dataset (Batch 11) for Word Atlas (#8039, #4387).

This module defines 32 curated heteronym lemmas (64 distinct variants)
expanding the curated heteronym SSOT from 328 to 360 lemmas.

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

CURATED_HETERONYMS_BATCH_11: dict[str, list[dict[str, Any]]] = {'попереносити': [{'headword': 'поперено́сити',
                   'short_label': 'перенести все або багато чогось в інше місце або на інший час (док.)',
                   'gloss': 'carry, transfer or postpone all or many items/events (perf.)',
                   'pos': 'verb',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[pɔpɛrɛˈnɔsɪtɪ]'},
                   'stress': {'form': 'поперено́сити',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/попереносити'},
                   'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                   'distinction_note': 'Позначає перенесення багатьох предметів або перенесення строків кількох подій '
                                       '(док. вид). Не плутати з «попереноси́ти» (тривалий час носити туди й сюди).',
                   'meaning': {'definitions': ['Перенести все або багато чого-небудь з одного місця в інше чи на інший '
                                               'час (доконаний вид).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ПОПЕРЕНО́СИТИ, о́шу, о́сиш, док., перех. Перенести '
                                                                 'багатьох, багато чого-небудь (не за один раз). Кращі '
                                                                 'картини з батькового флігеля дочки попереносили до '
                                                                 'себе (Н.-Лев., І, 1956, 376); Думає [Петро]; — '
                                                                 'Додому нести? Ні, то дуже довго буде. Попереношу '
                                                                 '[клунки] на могилу, нехай там перележать (Гр., Без '
                                                                 'хліба, 1958, 101).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None},
                   {'headword': 'попереноси́ти',
                    'short_label': 'переносити багато чого-небудь за довгий час (док.)',
                    'gloss': 'carry or haul many things over an extended period of time (perf.)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': {'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                    'pronunciation': {'ipa': '[pɔpɛrɛnɔˈsɪtɪ]'},
                    'stress': {'form': 'попереноси́ти',
                               'source': 'ВТС',
                               'url': 'https://slovnyk.me/dict/vts/попереносити'},
                    'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Позначає кумулятивну дію перенесення великої кількості речей протягом тривалого '
                                        'часу («скільки дідова спина попереносила за життя»; док. вид). Не плутати '
                                        'з «поперено́сити» (перенести всі або багато предметів в інше місце чи на інший строк).',
                    'meaning': {'definitions': ['Переносити багато чого-небудь за довгий час (доконаний вид).'], 'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ПОПЕРЕНОСИ́ТИ, ошу́, о́сиш, док., перех. Переноси́ти '
                                                                 'багато чого-небудь за довгий час. А скільки ж оті '
                                                                 'дідові, порепані руки поперетягали, а скільки ота '
                                                                 'дідова Матвієва спина попереносила… (Вишня, І, 1956, '
                                                                 '33).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None}],
 'поправний': [{'headword': 'попра́вний',
                'short_label': 'який можна виправити, піддатний виправленню',
                'gloss': 'correctable, remediable or improvable',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[pɔˈprɑu̯nɪj]'},
                'stress': {'form': 'попра́вний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/поправний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Означає такий, що піддається виправленню або може бути полагоджений чи виправлений '
                                    '(поправна помилка, поправне становище). Рідше — правильний, вправний. Не плутати '
                                    'з «поправни́й» (виправний, реформаторський або коригувальний коефіцієнт).',
                'meaning': {'definitions': ['Який можна виправити; піддатний виправленню.'], 'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОПРА́ВНИЙ, а, е. 1. Те саме, що випра́вний; // Якого '
                                                              'можна поповнити чим-небудь. Думки її, наче рої жалючих '
                                                              'ос, в’ються і жалять і сповнюють душу безнадійністю, '
                                                              'нічим не поправною втратою (Шиян, Баланда, 1957, 249). '
                                                              '2. рідко. Те саме, що пра́вильний. Коли говорить [пані '
                                                              'Марко], можна за нею писати. Її мова поправна, '
                                                              'інтересна (Коб., І, 1956, 247); [Меценат:] Чи ти б '
                                                              'хотів, щоб наші всі народи по-варварськи довіку '
                                                              'говорили?.. [Прокуратор:] Нехай мовчать, поки як слід '
                                                              'навчаться поправної латині! (Л. Укр., III, 1952, 452); '
                                                              '// Те саме, що впра́вний. Вона поглянула з суворістю '
                                                              'знавця.. — Чудово! Сильний хист і олівець поправний! '
                                                              '(Міцк., П. Тадеуш, перекл. Рильського, 1949, 108).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
                {'headword': 'поправни́й',
                 'short_label': 'виправний (заклад, роботи; рідко)',
                 'gloss': 'correctional, reformatory (penal/institution, e.g. correctional facility)',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[pɔprɐu̯ˈnɪj]'},
                 'stress': {'form': 'поправни́й', 'source': 'СУМ-20', 'url': 'https://slovnyk.me/dict/newsum/поправний'},
                 'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                 'distinction_note': 'Позначає виправний характер установ чи заходів (поправний заклад, поправні роботи). '
                                     'Не плутати з якісним значенням «попра́вний» (піддатний виправленню).',
                 'meaning': {'definitions': ['Те саме, що виправни́й (поправний заклад, поправні роботи; рідко).'], 'source': 'СУМ-20'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОПРАВНИ́Й, а́, е́, рідко. Те саме, що виправни́й. '
                                                              'По-новому висвітлює дослідник зв’язки письменниці '
                                                              '[Марка Вовчка] з О. В. Пассеком, підкреслюючи їхні щирі '
                                                              'стосунки, позитивно оцінюючи проекти реорганізації '
                                                              'тюрем і поправних закладів у Росії, складені ним (Рад. '
                                                              'літ-во, 7, 1965, 86).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'посвататися': [{'headword': 'посва́татися',
                  'short_label': 'звернутися з пропозицією одруження через старостів (док.)',
                  'gloss': 'propose marriage, send matchmakers for a bride (perf.)',
                  'pos': 'verb',
                  'cefr': 'B1',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[pɔˈswɑtɐtɪsʲɐ]'},
                  'stress': {'form': 'посва́татися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/посвататися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Позначає пропозицію шлюбу нареченій через сватів («пішов посвататися до '
                                      'козачки»; док. вид). Не плутати з «посвата́тися» (породичатися батькам).',
                  'meaning': {'definitions': ['Звернутися до дівчини або її батьків через сватів, прохаючи згоди на '
                                              'одруження (доконаний вид).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПОСВА́ТАТИСЯ, аюся, аєшся, док. Звернутися до батьків '
                                                                'дівчини, звичайно через старостів або взагалі через '
                                                                'посередників, прохаючи дати згоду на одруження з їх '
                                                                'дочкою. Той нероба, ледащо пошле старостів до '
                                                                'Олександри. На злість Насті посватається (Коцюб., І, '
                                                                '1955, 25); // Самому запропонувати себе в чоловіки '
                                                                'дівчині, жінці. Він посватався до Христі Стодольної '
                                                                '(Ле, Її кар’єра, 1947, 3).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'посвата́тися',
                  'short_label': 'породичатися, стати сватами через шлюб дітей (док.)',
                  'gloss': "become in-laws through the marriage of one's children (perf.)",
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[pɔswɐˈtɑtɪsʲɐ]'},
                  'stress': {'form': 'посвата́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/посвататися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає стати сватами, вступити у свояцтво батькам наречених між собою («вони '
                                      'посваталися ще торік»; док. вид). Не плутати з залицянням і сватанням дівчини '
                                      '«посва́татися».',
                  'meaning': {'definitions': ['Стати сватами, поріднитися через одруження дітей (доконаний вид).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПОСВАТА́ТИСЯ, а́ємося, а́єтеся, док., розм. 1. Стати '
                                                                'сватами. У вас дочка, а в нас син, то може й '
                                                                'посватаємося (Сл.Гр.). 2. Подружитися, '
                                                                'заприятелювати. Зо всіми миттю побратались, '
                                                                'Посватались і покумались [троянці], Мов зроду тутечка '
                                                                'жили (Котл., І, 1952, 114).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'потикати': [{'headword': 'поти́кати',
               'short_label': 'повстромляти багато чогось або тикати якийсь час (док., розм.)',
               'gloss': 'stick or poke repeatedly, jab into many places (perf., colloq.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈtɪkɐtɪ]'},
               'stress': {'form': 'поти́кати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/потикати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає повстромляти предмети у землю чи стіну («потикати кілля») або штрикати '
                                   'пальцем якийсь час (док. вид). Не плутати з фразеологізмом «потика́ти носа».',
               'meaning': {'definitions': ['Встромити, впихнути багато чого-небудь у середину або тикати якийсь час '
                                           '(доконаний вид).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОТИ́КАТИ, аю, аєш, док., перех., розм. 1. Поколоти в '
                                                             'багатьох місцях. 2. Встромити, впихнути багато чогось у '
                                                             'середину, в глиб чого-небудь. Так рідко посходив '
                                                             '[часник], наче нечистий кіллям потикав (Номис, 1864, № '
                                                             '10187). 3. Тикати якийсь час, тикнути кілька разів.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'потика́ти',
               'short_label': "(не) потикати носа кудись — (не) показуватися, не з'являтися (недок.)",
               'gloss': "show oneself, poke one's nose somewhere (imperf., phr.)",
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔtɪˈkɑtɪ]'},
               'stress': {'form': 'потика́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/потикати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
               'distinction_note': "Вживається у стійкому виразі: «не потикати носа» — не насмілюватися з'являтися або "
                                   'не показуватися куди-небудь (недок. вид; док. «поткнути»). Не плутати з дією '
                                   'встромляння «поти́кати».',
               'meaning': {'definitions': ["З'являтися де-небудь, показуватися комусь (звичайно у фразеологізмі: не "
                                           'потикати носа; недоконаний вид).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОТИКА́ТИ, а́ю, а́єш, недок., ПОТКНУ́ТИ, ну́, не́ш, '
                                                             'док.: [Не] потика́ти (поткну́ти) но́са куди, до кого — '
                                                             '[не] з’являтися де-небудь, [не] приходити до когось. — А '
                                                             'там ще зима: сніг, морози. І знову сиди в хаті, не '
                                                             'потикай носа надвір, бо відморозиш (Мирний, III, 1954, '
                                                             '294); [Ганна:] Я весь свій вік роблю, а маю півморга. А '
                                                             'той пан десь у Кракові жив, сюди й носа не потикав, а '
                                                             'хліб з землі йому віддай (Мокр., П’єси, 1959, 113); — '
                                                             'Полізли, жевжики [піонери], у таку страшну печеру, що я, '
                                                             'старий, побоявся б у неї носа поткнути, — пояснив '
                                                             'учительці Харитон Макарович (Мокр., Острів.., 1961, 85); '
                                                             'Потика́ти [свого́] но́са куди — втручатися в щось. — Не '
                                                             'потикай носа до чужого проса!.. (Вол., Озеро.., 1959, '
                                                             '39).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'потріпати': [{'headword': 'потрі́пати',
                'short_label': 'тріпнути кілька разів крилами, руками чи волоссям (док.)',
                'gloss': 'flutter, flap or wag a few times (perf.)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[pɔˈtrʲipɐtɪ]'},
                'stress': {'form': 'потрі́пати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/потріпати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає тріпнути кілька разів крилами або поплескати дружньо по плечу («півень '
                                    'потріпав крилами»; док. вид). Не плутати зі зношуванням одягу чи пошарпанням у '
                                    'бою «потріпа́ти».',
                'meaning': {'definitions': ['Тріпнути кілька разів; затріпотіти (доконаний вид).'], 'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОТРІ́ПАТИ, аю, аєш, док., чим. Трі́пнути кілька разів; '
                                                              'затріпотіти. Потріпав [півень] крилами, закукурікав та '
                                                              '— шубовсть у Лаврінові огірки (Н.-Лев., II, 1956, 372); '
                                                              '[Баба:] Він тоді палюгою її [сучку] по ногах, вона '
                                                              'заскавучала, потріпала ногою і щезла… (Вас., III, 1960, '
                                                              '51); — Ще раз повторюю, що не розумію вас, — сказав '
                                                              'ображено Кемпер, поворушив пальцями, потріпав ними, '
                                                              'наче струшував підозру, що могла до них прилипнути '
                                                              '(Загреб., Шепіт, 1966, 377).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'потріпа́ти',
                'short_label': 'обтріпати, пошарпати (одяг) або пошарпати ворога в бою (док., розм.)',
                'gloss': 'fray, wear out (garments) or batter/roughen up in battle (colloq., perf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[pɔtrʲiˈpɑtɪ]'},
                'stress': {'form': 'потріпа́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/потріпати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає привести в стан зношеності, обтріпати краї одягу або виснажити когось у '
                                    'випробуваннях чи битвах (док. вид). Не плутати з рухом крил чи пальців '
                                    '«потрі́пати».',
                'meaning': {'definitions': ['Пошкодити по краях тертям, носінням; обтріпати; перен. завдати відчутних '
                                            'втрат, виснажити (доконаний вид; розм.).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПОТРІПА́ТИ, а́ю, а́єш, док. 1. перех. і неперех. '
                                                              'Тріпати, шарпати якийсь час. Я взяв до рук жмут соломи, '
                                                              'потріпав ним об коліно і, сам не знаю для чого, понюхав '
                                                              '(Збан., Єдина, 1959, 346); // Завдати шкоди (про бурю, '
                                                              'шторм); // безос. Чотирищогловий бриг «Грифтен» так '
                                                              'потріпало в Біскайській затоці, що команді довелося '
                                                              'кинути якір в Гібралтарі.. і приступити до ремонту '
                                                              'судна (Знання.., 8, 1970, 29); // перен. Завдати втрат '
                                                              'під час бойових дій; // перен. Знесилити, знервувати '
                                                              'тяжкими переживаннями, випробуваннями і т. ін. '
                                                              'Безпосередня революційна боротьба і робота позбавили '
                                                              'активіста можливості поповнювати свою освіту. Роки '
                                                              'революції також дуже потріпали його фізично (КПУ в '
                                                              'резол. і рішен.., 1958, 202). 2. перех. Ласкаво '
                                                              'поплескати, погладити кого-небудь. Остап розплющив очі. '
                                                              'Це так врадувало стару циганку, що вона забелькотала '
                                                              'щось жваво.. й радісно потріпала Соломію по плечах '
                                                              '(Коцюб., І, 1955, 370); Хмельницький потріпав рукою '
                                                              'гриву, заплетену червоними стрічками (Рибак, Переясл. '
                                                              'Рада, 1953, 566). 3. перех. Порвати, обтріпати, '
                                                              'поносивши, покористувавшися. Потріпати пальто; '
                                                              'Потріпати книжку. 4. перех., розм. Побити (не сильно). '
                                                              '— Я вхопив їх обох за карки, думав собі: от діти. Був '
                                                              'би потріпав їх трохи та й пустив (Фр., VI, 1951, 146).',
                                                'sovietization_risk': 1,
                                                'keywords': ['кпу'],
                                                'historical_note': 'Радянський словник СУМ-11 ілюструє переносне '
                                                                   'слововживання цитатою з партійних резолюцій '
                                                                   'Компартії (КПУ).'},
                'pre_soviet_witness': None}],
 'потіпати': [{'headword': 'поті́пати',
               'short_label': 'тіпати, трусити або смикати якийсь час (док., розм.)',
               'gloss': 'shake, jolt or twitch for some time (colloq., perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔˈtʲipɐtɪ]'},
               'stress': {'form': 'поті́пати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/потіпати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Означає тіпати, смикати або струшувати щось протягом деякого часу (док. вид). Не '
                                   'плутати з очищенням прядива чи побиттям «потіпа́ти».',
               'meaning': {'definitions': ['Тіпати якийсь час (доконаний вид; розм.).'], 'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОТІ́ПАТИ, аю, аєш, док., перех і неперех., розм. '
                                                             'Ті́пати якийсь час.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'потіпа́ти',
               'short_label': 'очистити тіпанням льон або коноплі; побити когось (док., розм.)',
               'gloss': 'scutch all flax/hemp clean; thrash/beat someone (colloq., perf.)',
               'pos': 'verb',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[pɔtʲiˈpɑtɪ]'},
               'stress': {'form': 'потіпа́ти',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/потіпати'},
               'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
               'distinction_note': 'Позначає обробку волокна тіпанням (очистити прядиво від костриці) або переносне '
                                   'побиття палицею (док. вид). Не плутати з короткочасним струшуванням «поті́пати».',
               'meaning': {'definitions': ['Очистити від костриці тіпанням (стебла льону, конопель); перен. побити '
                                           'кого-небудь (доконаний вид).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'ПОТІПА́ТИ, а́ю, а́єш, док., перех. 1. Очистити від '
                                                             'сторонніх домішок тіпанням усе або багато чогось (стебла '
                                                             'льону, конопель і т. ін.). На́ тобі круг прядива: щоб ти '
                                                             'його пом’яла, потіпала (Сл. Гр.). 2. перен. Побити '
                                                             'кого-небудь (звичайно палкою). — Мені б тільки пана '
                                                             'потіпати, я з нього душу витрясу (Панч, Гомон. Україна, '
                                                             '1954, 112). 3. перен. Зробити виснаженим, підтоптаним, '
                                                             'пошарпаним. Життя таки добре потіпало його (Дім., Ідол, '
                                                             '1961, 125).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Потіпати, -пАю, -єш, гл. Потрепать. На тобі круг прядіва: щоб ти його '
                                               "пом'яла, потіпала. Рудч. Ск. II. 44. Потіпати за бороду. ХС. IV. 23.",
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}}],
 'пречудний': [{'headword': 'пречу́дний',
                'short_label': 'дуже гарний, дивовижний, пречудовий (розм.)',
                'gloss': 'wondrous, marvelous, exceedingly beautiful (colloq.)',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɛˈt͡ʃudnɪj]'},
                'stress': {'form': 'пречу́дний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пречудний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Означає прекрасний, пречудовий («пречудний ранок був, сміялось небо»; від пре- + '
                                    'чудовий/чудний). Не плутати з дивакуватим значенням «пречудни́й».',
                'meaning': {'definitions': ['Те саме, що пречудо́вий (дуже гарний, прекрасний; розм.).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРЕЧУ́ДНИЙ, а, е, розм. Те саме, що пречудо́вий. '
                                                              'Пречудний ранок був, сміялось небо, Співали пташки, '
                                                              '..Іскрилася роса на всіх листочках (Фр., XIII, 1954, '
                                                              '220).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'пречудни́й',
                'short_label': 'дуже дивний, чудернацький, дивакуватий (розм.)',
                'gloss': 'exceedingly strange, odd, eccentric or bizarre (colloq.)',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɛt͡ʃʊdˈnɪj]'},
                'stress': {'form': 'пречудни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/пречудний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Означає надзвичайно дивний або химерний («пречудна нотатка, пречудні звичаї»; від '
                                    'пре- + чудни́й). Не плутати з прекрасним «пречу́дний».',
                'meaning': {'definitions': ['Дуже чудни́й (дивний, чудернацький; розм.).'], 'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРЕЧУДНИ́Й, а, е, розм. Дуже чудни́й. [Маня (між тим '
                                                              'ухопила газету і погляділа):] Його портрет.. А збоку '
                                                              'замість біографії, адіть, яка нотатка, — пречудна '
                                                              'нотатка, слухайте! (Фр., IX, 1952, 17).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'припадковий': [{'headword': 'припа́дковий',
                  'short_label': 'стосовний до припадку (медичного нападу або судом)',
                  'gloss': 'paroxysmal, relating to fits, spasms or seizures',
                  'pos': 'adj',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[prɪˈpɑdkɔwɪj]'},
                  'stress': {'form': 'припа́дковий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/припадковий'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Медичний термін: стосовний до раптового нападу хвороби (припадковий біль '
                                      'голови, припадковий стан). Не плутати з випадковим «припадко́вий».',
                  'meaning': {'definitions': ['Прикметник до припа́док (раптовий напад хвороби, судом тощо).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПРИПА́ДКОВИЙ, а, е. Прикм. до припа́док¹. На '
                                                                'припадковий біль голови у Вронського зараз ладила '
                                                                '[мадярка] лимонаду (Мак., Вибр., 1954, 121).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'припадко́вий',
                  'short_label': 'випадковий, ненавмисний, побіжний (діал., зах.)',
                  'gloss': 'accidental, incidental, occasional (dial.)',
                  'pos': 'adj',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[prɪpɐdˈkɔwɪj]'},
                  'stress': {'form': 'припадко́вий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/припадковий'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Діалектне та класичне західноукраїнське слово: випадковий, несподіваний '
                                      '(«припадковий гість, припадкова зустріч»; від припадок — випадок). Не плутати з '
                                      'медичним спазмом «припа́дковий».',
                  'meaning': {'definitions': ['Випадковий, ненавмисний (діал.).'], 'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПРИПАДКО́ВИЙ, а, е, діал. Випадковий. Що вона має '
                                                                'тепер шукати в парку? Тепер осінь, парк майже '
                                                                'порожній, а тих кілька припадкових гостей, що '
                                                                'являються в нім ще десь-не-десь, то ще не товариство '
                                                                '(Коб., І, 1956, 408); Тарас думав спочатку, що ся '
                                                                'стріча з товаришами то тільки така припадкова, але '
                                                                'невдовзі річ вияснилася, що то було все умовлене, '
                                                                'щоби ще раз попрощатися з Тарасом (Ков., Світ.., '
                                                                '1960, 70).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'присікання': [{'headword': 'присі́кання',
                 'short_label': 'набридання причіпками, докучання, чіпляння (розм.)',
                 'gloss': 'faultfinding, nagging, picking quarrels (colloq.)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[prɪˈsʲikɐnʲːɐ]'},
                 'stress': {'form': 'присі́кання', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/присікання'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'середній',
                                             'animacy': 'inanimate',
                                             'cases': {'називний': {'singular': 'присі́кання'},
                                                       'родовий': {'singular': 'присі́кання'},
                                                       'давальний': {'singular': 'присі́канню'},
                                                       'знахідний': {'singular': 'присі́кання'},
                                                       'орудний': {'singular': 'присі́канням'},
                                                       'місцевий': {'singular': 'присі́канні'},
                                                       'кличний': {'singular': 'присі́кання'}}}},
                 'distinction_note': 'Віддієслівний іменник від «присі́катися» (чіплятися до когось безпідставно, '
                                     'докоряти; розм.). Не плутати з підтинанням гілок «присіка́ння».',
                 'meaning': {'definitions': ['Дія за значенням присі́катися (набридати причіпками, чіплятися до '
                                             'когось; розм.).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПРИСІ́КАННЯ, я, с., розм. Дія за знач. присі́катися. '
                                                               'Коли присікання господаря набрали агресивного '
                                                               'характеру, Швейк скинув його зі сходів униз і почав '
                                                               'оглядати верхні кімнати (Гашек, Пригоди.. Швейка, '
                                                               'перекл. Масляка, 1958, 512).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'присіка́ння',
                 'short_label': 'відсікання або підрубування кінців (гілок, дерев, рослин)',
                 'gloss': 'pruning, lopping off or truncation of branch ends',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[prɪsʲiˈkɑnʲːɐ]'},
                 'stress': {'form': 'присіка́ння', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/присікання'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'середній',
                                             'animacy': 'inanimate',
                                             'cases': {'називний': {'singular': 'присіка́ння'},
                                                       'родовий': {'singular': 'присіка́ння'},
                                                       'давальний': {'singular': 'присіка́нню'},
                                                       'знахідний': {'singular': 'присіка́ння'},
                                                       'орудний': {'singular': 'присіка́нням'},
                                                       'місцевий': {'singular': 'присіка́нні'},
                                                       'кличний': {'singular': 'присіка́ння'}}}},
                 'distinction_note': 'Віддієслівний іменник від «присіка́ти» (відрубувати або вкорочувати краї гілок, '
                                     'підтинати). Не плутати з набриданням докорами «присі́кання».',
                 'meaning': {'definitions': ['Дія за значенням присіка́ти (відсікати, підрубувати кінці чогось).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПРИСІКА́ННЯ, я, с. Дія за знач. присіка́ти.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'провозитися': [{'headword': 'прово́зитися',
                  'short_label': 'перевозитися транспортом через контрольний пункт (недок., пас.)',
                  'gloss': 'be transported, conveyed or carted through (passive, imperf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[prɔˈwɔzɪtɪsʲɐ]'},
                  'stress': {'form': 'прово́зитися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/провозитися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Пасивна форма від дієслова «прово́зити» (доставляти вантаж або пасажирів через '
                                      'митницю чи кордон). Не плутати з витрачанням часу біля речей «провози́тися».',
                  'meaning': {'definitions': ['Пасивна форма до прово́зити (переміщатися за допомогою транспорту).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПРОВО́ЗИТИСЯ, иться, недок. Пас. до прово́зити. Вони '
                                                                '[удільні князі].. збирали на свою користь мито з '
                                                                'товарів, що провозилися через їх князівства (Іст. '
                                                                'УРСР, І, 1953, 109).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'провози́тися',
                  'short_label': 'витратити багато часу, марудно пораючись із чимсь (док., розм.)',
                  'gloss': 'spend a lot of time fussing or tinkering with something (colloq., perf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[prɔwɔˈzɪtɪsʲɐ]'},
                  'stress': {'form': 'провози́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/провозитися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає змарнувати час на ремонт, прибирання або клопіт біля когось чи чогось '
                                      '(«біля воза до обіду провозилися»; док. вид). Не плутати з транспортуванням '
                                      '«прово́зитися».',
                  'meaning': {'definitions': ['Витратити багато часу, займаючись ким-, чим-небудь (доконаний вид; '
                                              'розм.).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПРОВОЗИ́ТИСЯ, ожу́ся, о́зишся, док., розм. Возитися '
                                                                '(у 2 знач.) якийсь час. Цей день так і минув: біля '
                                                                'воза до обіду провозилися, по обіді в клуні віяли '
                                                                'зерно (Головко, II, 1957, 136); Повернувся її чоловік '
                                                                'від Збруча на кованій бричці й до самого ранку '
                                                                'провозився за хатою, закопуючи награбоване добро '
                                                                '(Цюпа, Назустріч.., 1958, 62).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'продихати': [{'headword': 'проди́хати',
                'short_label': 'проіснувати або прожити якийсь час (док., розм.)',
                'gloss': 'survive, stay alive or hang on for some time (colloq., perf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɔˈdɪxɐtɪ]'},
                'stress': {'form': 'проди́хати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/продихати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                'distinction_note': 'Означає прожити, утриматися при житті певний обмежений час («хто знає, чи ще '
                                    'тиждень продихає»; док. вид). Не плутати з продуванням вітром «продиха́ти».',
                'meaning': {'definitions': ['Проіснувати якийсь час; прожити (доконаний вид; розм.).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРОДИ́ХАТИ, проди́хаю, проди́хаєш і проди́шу, '
                                                              'проди́шеш, док. Проіснувати якийсь час; прожити. — Моя '
                                                              'стара, бідна, догорає.. Хто знає, чи ще тиждень '
                                                              'продихає (Фр., І, 1955, 135).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'продиха́ти',
                'short_label': 'продувати, освіжати вітром або дихати крізь щось (недок.)',
                'gloss': 'blow a fresh breeze through, air out; breathe through (imperf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɔdɪˈxɑtɪ]'},
                'stress': {'form': 'продиха́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/продихати'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': 'Позначає провіювання вітром («вітерець продихає холодком») або дихання крізь шар '
                                    'тканини чи льоду (недок. вид). Не плутати з дієсловом виживання «проди́хати».',
                'meaning': {'definitions': ['Продувати, освіжати струменем повітря або дихати крізь щось (недоконаний '
                                            'вид; розм.).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРОДИХА́ТИ, а́ю, а́єш, недок., перех. і неперех., розм. '
                                                              'Те саме, що продува́ти. [Микита:] Чи бач, а тут у '
                                                              'холодочку не так пече, і вітерець продихає (Сам., II, '
                                                              '1958, 162); Вітерець устиг обтрусити росу з віт, '
                                                              'приємно продихав крізь дерева (Ле, Мої листи, 1945, '
                                                              '120); Понапинали [діти] сорочки на коліна, продихають '
                                                              'на шибках ясні кружечки (Вас., II, 1959, 144).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'продублювати': [{'headword': 'проду́блювати',
                   'short_label': 'обробляти дубленням; перен. огрублювати шкіру сонцем і вітром (недок.)',
                   'gloss': 'tan thoroughly (leather/flax); weather-harden skin (imperf.)',
                   'pos': 'verb',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[prɔˈdublʲʊwɐtɪ]'},
                   'stress': {'form': 'проду́блювати',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/продублювати'},
                   'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                   'distinction_note': 'Термін чинбарства: обробляти дубильними речовинами, або переносне огрубіння '
                                       'обличчя від спеки («кого спека продублює»; недок. вид, док. «продубити»). Не '
                                       'плутати зі створенням копій «продублюва́ти».',
                   'meaning': {'definitions': ['Обробляти дубленням (шкіри, льон); перен. робити шкіру грубою під дією '
                                               'вітру або сонця (недоконаний вид).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ПРОДУ́БЛЮВАТИ, юю, юєш, недок., ПРОДУБИ́ТИ, дублю́, '
                                                                 'ду́биш; мн. проду́блять; док., перех. Обробляти '
                                                                 'дубленням. Продубити шкіри; Продубити льон на '
                                                                 'килими; // перен. Робити шкіру людини грубою, '
                                                                 'шорсткою (про дію вітру, холоду, сонця і т. ін.). '
                                                                 'Чабан — це той,.. кого спека продублює і осінні '
                                                                 'мряки пронизують до кісток (Гончар, Тронка, 1963, '
                                                                 '15).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None},
                  {'headword': 'продублюва́ти',
                   'short_label': 'зробити дублікат, повторити або озвучити фільм іншою мовою (док.)',
                   'gloss': 'duplicate, understudy or dub into Ukrainian (perf.)',
                   'pos': 'verb',
                   'cefr': 'B1',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[prɔdʊblʲʊˈwɑtɪ]'},
                   'stress': {'form': 'продублюва́ти',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/продублювати'},
                   'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                   'distinction_note': 'Позначає створення копії документа, заміну актора дублером або український '
                                       'дубляж фільму (док. вид від дублювати). Не плутати з дубленням шкіри '
                                       '«проду́блювати».',
                   'meaning': {'definitions': ['Зробити дублікат, повторити дію або виконати переклад і озвучення '
                                               'кінофільму (доконаний вид).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ПРОДУБЛЮВА́ТИ, ю́ю, ю́єш, перех. Док. до дублюва́ти. '
                                                                 'О 9-й вечора пролунав постріл «Авроры». Його '
                                                                 'продублював постріл з Петропавловської фортеці '
                                                                 '(Вітч., 11, 1967, 196); Продублювати фільм.',
                                                   'sovietization_risk': 1,
                                                   'keywords': ['аврора'],
                                                   'historical_note': 'СУМ-11 ілюструє дублювання цитатою про '
                                                                      '«історичний залп Аврори» — ключовий '
                                                                      'ідеологічний міф більшовицької революції.'},
                   'pre_soviet_witness': None}],
 'прозірний': [{'headword': 'прозі́рний',
                'short_label': 'прозорий, чистий, ясний (A2)',
                'gloss': 'transparent, limpid, clear (water, sky, air)',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɔˈzʲirnɪj]'},
                'stress': {'form': 'прозі́рний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/прозірний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Означає прозорий, ясний, чистий (про повітря, воду, небо). Наголос падає на '
                                    'корінь: прозі́рний.',
                'meaning': {'definitions': ['Те саме, що прозо́рий 1 (про воду, небо, повітря).'], 'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРОЗІ́РНИЙ, а, е. Те саме, що прозо́рий 1. З берегом '
                                                              'хвиля прозірна шуткує, Ластиться наче до його вона '
                                                              '(Манж., Тв., 1955, 102); Березневого неба глибінь '
                                                              'прохолодна й прозірна (Перв., І, 1958, 216).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'прозірни́й',
                'short_label': 'проникний для зору, видимий наскрізь (B2)',
                'gloss': 'penetrable by sight, see-through (can be seen through)',
                'pos': 'adj',
                'cefr': 'C1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[prɔzʲirˈnɪj]'},
                'stress': {'form': 'прозірни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/прозірний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Означає такий, крізь який або в який можна проникнути зором (видимий наскрізь). '
                                    'Наголос падає на закінчення: прозірни́й. Не плутати з «прозорливий» '
                                    '(далекоглядний).',
                'meaning': {'definitions': ['В який (крізь який) можна проникнути зором; проникний для зору.'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ПРОЗІРНИ́Й, а́, е́. В який (крізь який) можна '
                                                              'проникнути зором.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'проповзати': [{'headword': 'пропо́взати',
                 'short_label': 'повзати якийсь час (док.)',
                 'gloss': 'crawl or creep around for a while (perf.)',
                 'pos': 'verb',
                 'cefr': 'B1',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[prɔˈpɔu̯zɐtɪ]'},
                 'stress': {'form': 'пропо́взати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/проповзати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Означає переміщатися повзком протягом певного періоду часу («дитина проповзала '
                                     'пів дня»; док. вид). Не плутати з подоланням відстані повзком «проповза́ти».',
                 'meaning': {'definitions': ['Повзати якийсь час (доконаний вид).'], 'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПРОПО́ВЗАТИ, аю, аєш, док. Повзати якийсь час.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'проповза́ти',
                 'short_label': 'переміщатися повзком крізь щось або повз когось (недок.)',
                 'gloss': 'creep through, crawl past or slide along (imperf.)',
                 'pos': 'verb',
                 'cefr': 'B1',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[prɔpɔu̯ˈzɑtɪ]'},
                 'stress': {'form': 'проповза́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/проповзати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Позначає подолання простору або переповзання перешкоди (недок. вид, док. '
                                     '«проповзти»: «вуж проповзає по дорозі»). Не плутати з часовим значенням '
                                     '«пропо́взати».',
                 'meaning': {'definitions': ['Переміщатися повзком по поверхні, просуватися крізь вузьке місце '
                                             '(недоконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ПРОПОВЗА́ТИ, а́ю, а́єш і рідко ПРОПО́ВЗУВАТИ, ую, уєш, '
                                                               'недок., ПРОПОВЗТИ́, зу́, зе́ш, док. 1. Переміщатися '
                                                               'повзком де-небудь, по поверхні чогось і т. ін. (про '
                                                               'комах, плазунів). Одразу хоче [дівча] оповісти усе: і '
                                                               'як жук проповзав по дорозі, як черевичок у воду упав, '
                                                               'і як скакали вівці з гори, а сонце світило поміж '
                                                               'гіллям груші (Хотк., II, 1966, 304); Вона побачила, як '
                                                               'на траві біля своєї оселі, важко здригаючись, проповз '
                                                               'на підігнутих ніжках джміль (Стельмах, І, 1962, 525); '
                                                               '*Образно. Не проповзе гадюкою у житі війна до нас, — '
                                                               'ми в цьому поклялись (Сос., Солов. далі, 1917, 67); // '
                                                               'перен. Повільно рухатися де-небудь, переміщатися через '
                                                               'щось і т. ін. (про засоби пересування). Селом '
                                                               'проповзали обози, ішли військові частини (Коз., Вибр., '
                                                               '1947, 22); Танки важкі проповзли край окопу (Криж., '
                                                               'Срібне весілля, 1957, 285); // перен. Повільно '
                                                               'просуватися над ким-, чим-небудь (про хмари, туман і '
                                                               'т. ін.). Шпилі гір уже притрусило сніжком; ..блукали '
                                                               'сірі осінні хмари; вони проповзали над лісами, '
                                                               'чіпляючись за верховіття (Скл., Карпати, II, 1954, '
                                                               '106); Не одна ще біла хмарка проповзе над верхом '
                                                               'кичери, не один раз нагріється під сонцем і знов '
                                                               'охолоне камінь коло потоку (Хотк., II, 1966, 307); // '
                                                               'перев. недок., перен. Ледь помітно звиватися (про '
                                                               'стежку, річку і т. ін.). Підносилися над селом дві '
                                                               'великі гори, а між ними проповзала, мов вуж, '
                                                               'вузесенька річечка (Літ. Укр., 10.III 1970, 2); Стежка '
                                                               'обминала сього поваленого велетня і проповзувала аж '
                                                               'туди, де кінчився його пень (Фр., III, 1950, 88). 2. '
                                                               'Повзком пересуватися, переміщатися у якому-небудь '
                                                               'напрямку, десь, повз когось, щось і т. ін. (про '
                                                               'людей). Телефоніст, тримаючись рукою за провід, '
                                                               'проповз назад до села шукати обрив (Трубл., І, 1955, '
                                                               '43); Проповз по траншеї хлопець, розносячи патрони (Ю. '
                                                               'Янов., І, 1958, 212); // тільки док. Повзком долати '
                                                               'якусь відстань. Раз у раз спиняючися, перечікуючи і '
                                                               'припадаючи до землі, проповзла вона метрів із '
                                                               'п’ятнадцять (Смолич, І, 1958, 92); Десять кроків, які '
                                                               'одділяли його від яблуні, він проповз на животі '
                                                               '(Сенч., На Бат. горі, 1960, 23). 3. перен. Крадькома, '
                                                               'непомітно проникати, потрапляти куди-небудь. Треба '
                                                               'проповзти в розташування ворога і знищити без усякого '
                                                               'шуму два-три кулеметні гнізда, щоб відкрити прохід для '
                                                               'несподіваного наступу (Багмут, Опов., 1959, 56).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'прополювати': [{'headword': 'пропо́лювати',
                  'short_label': "очищати посіви або грядки від бур'янів сапою чи руками (недок.)",
                  'gloss': 'weed out, clear crops and beds of weeds (imperf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[prɔˈpɔlʲʊwɐtɪ]'},
                  'stress': {'form': 'пропо́лювати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/прополювати'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': "Агрономічна дія: видаляти бур'яни з посівів (недок. вид від «прополоти»). Не "
                                      'плутати з мисливським «прополюва́ти».',
                  'meaning': {'definitions': ['Очищати посіви від бур’янів, вириваючи їх руками або сапаючи '
                                              '(недоконаний вид).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПРОПО́ЛЮВАТИ, юю, юєш, недок., ПРОПОЛО́ТИ, полю́, '
                                                                'по́леш, док., перех. Очищати (звичайно посіви) від '
                                                                'бур’янів, вириваючи їх руками, стинаючи сапою, '
                                                                'механізмами або обробляючи хімікатами. Марія '
                                                                'оповідала про обробіток плантацій. Шість раз '
                                                                'прополювали, поки зійшла над землею гичка (Кучер, '
                                                                'Зол. руки, 1948, 212); Ліна клопочеться біля своїх '
                                                                'гладіолусів, а батько, голий до пояса, в чалмі '
                                                                'якійсь, мов фелах, прополює сапою картоплю (Гончар, '
                                                                'Тронка, 1963, 164); Топчи, милий, доріженьку, а я '
                                                                'свою прополю (Чуб., V, 1874, 274); Ланка за літо '
                                                                'дванадцять раз просапала й прополола буряки (Ю. '
                                                                'Янов., II, 1954, 232); *Образно. Отак, коли поет не '
                                                                'прополює сапою думок своїх, можуть вирости бур’яни у '
                                                                'його творі і заглушити основну думку, що зосталась '
                                                                'забутим острівцем під сонцем на горбочку… (Тич., III, '
                                                                '1957, 378); // Знищувати бур’яни, вириваючи їх '
                                                                'руками, стинаючи сапою або обробляючи хімікатами. '
                                                                'Рости, гойдайся, жито, З тобою добре жити, Тобі я '
                                                                'трошки пособлю — Навкруг волошки прополю… (Стельмах, '
                                                                'V, 1963, 392); // Проріджувати, вириваючи частину '
                                                                'рослин. Прополювати буряки.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'прополюва́ти',
                  'short_label': 'втратити щось на полюванні або полювати якийсь час (док., розм.)',
                  'gloss': 'lose while hunting or hunt for some time (colloq., perf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[prɔpɔlʲʊˈwɑtɪ]'},
                  'stress': {'form': 'прополюва́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/прополювати'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Мисливське розмовне слово від «полювати»: згубити річ у лісі або провести час '
                                      'на полюванні («прополював капелюх»; док. вид). Не плутати з прополюванням '
                                      'городу «пропо́лювати».',
                  'meaning': {'definitions': ['Втратити що-небудь під час полювання або полювати якийсь час (доконаний '
                                              'вид; розм.).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ПРОПОЛЮВА́ТИ, ю́ю, ю́єш, док. 1. перех., розм. '
                                                                'Втратити що-небудь внаслідок або в процесі полювання. '
                                                                'Прополював [капелюх]. І хто ті рушниці вигадав?! '
                                                                '(Вишня, II, 1956, 126). 2. неперех. Полювати якийсь '
                                                                'час.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'розбірний': [{'headword': 'розбі́рний',
                'short_label': 'розбірливий, чіткий для читання (почерк) або вибагливий',
                'gloss': 'legible, clear to read or discerning/discriminating',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[rɔzˈbirnɪj]'},
                'stress': {'form': 'розбі́рний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розбірний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Означає чіткий, зрозумілий для сприйняття (розбірний почерк, розбірний підпис) '
                                    'або критичний/аналітичний. Не плутати з розкладною конструкцією «розбірни́й».',
                'meaning': {'definitions': ['Те саме, що розбі́рливий (чіткий, зрозумілий; вибагливий).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'РОЗБІ́РНИЙ, а, е. Те саме, що розбі́рливий.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'розбірни́й',
                'short_label': 'який можна легко розібрати на складові частини й знову зібрати',
                'gloss': 'demountable, collapsible, sectional or dismountable',
                'pos': 'adj',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[rɔzbirˈnɪj]'},
                'stress': {'form': 'розбірни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розбірний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Технічний прикметник: такий, що розкладається на окремі елементи для зручності '
                                    'перевезення (розбірний міст, розбірна модель, розбірні меблі). Не плутати з '
                                    'якісним почерком «розбі́рний».',
                'meaning': {'definitions': ['Який можна легко розібрати і знову зібрати (про конструкцію, меблі '
                                            'тощо).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'РОЗБІРНИ́Й, а́, е́. Який можна легко розібрати і знову '
                                                              'зібрати. Гуртківці вже зробили розбірну модель трактора '
                                                              '(Донч., V, 1957, 365); Було б добре, якби організації, '
                                                              'покликані забезпечувати колгоспи тарою під фрукти, '
                                                              'розробили кілька зразків розбірних контейнерів '
                                                              '(Хлібороб Укр., 8, 1969, 22).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'розвозитися': [{'headword': 'розво́зитися',
                  'short_label': 'доставлятися або розвозитися транспортом по місцях (недок., пас.)',
                  'gloss': 'be delivered, distributed or carted to places (passive, imperf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[rɔzˈwɔzɪtɪsʲɐ]'},
                  'stress': {'form': 'розво́зитися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розвозитися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Пасивна форма від дієслова «розвозити» (вантажі розвозяться по крамницях). Не '
                                      'плутати з марудним зволіканням «розвози́тися».',
                  'meaning': {'definitions': ['Пасивна форма до розво́зити (розподілятися транспортом).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'РОЗВО́ЗИТИСЯ, иться, недок. Пас. до розво́зити 1.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'розвози́тися',
                  'short_label': 'витратити багато часу, займаючись чимось / марудитися (B2)',
                  'gloss': 'spend excessive time fussing or dawdling over something (colloq.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[rɔzwɔˈzɪtɪsʲɐ]'},
                  'stress': {'form': 'розвози́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розвозитися'},
                  'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає витрачати надмірно багато часу, клопочучись або марудячись коло когось '
                                      'чи чогось. Наголос на -зи́тися: розвози́тися.',
                  'meaning': {'definitions': ['Витратити багато часу, займаючись ким-, чим-небудь (розм., рідко).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'РОЗВОЗИ́ТИСЯ, вожу́ся, во́зишся, док., розм., рідко. '
                                                                'Витратити багато часу, займаючись ким-, чим-небудь.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'розвідниця': [{'headword': 'розві́дниця',
                 'short_label': 'жінка-розвідниця (військ./геол.) (A2)',
                 'gloss': 'female reconnaissance scout, intelligence operative',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzˈwʲidnɪt͡sʲɐ]'},
                 'stress': {'form': 'розві́дниця', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розвідниця'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'жіночий',
                                             'animacy': 'animate',
                                             'cases': {'називний': {'singular': 'розві́дниця'},
                                                       'родовий': {'singular': 'розві́дниці'},
                                                       'давальний': {'singular': 'розві́дниці'},
                                                       'знахідний': {'singular': 'розві́дницю'},
                                                       'орудний': {'singular': 'розві́дницею'},
                                                       'місцевий': {'singular': 'розві́дниці'},
                                                       'кличний': {'singular': 'розві́днице'}}}},
                 'distinction_note': 'Означає жінку-розвідницю (працівницю розвідки: військової чи геологічної). '
                                     'Наголос падає на корінь: розві́дниця.',
                 'meaning': {'definitions': ['Жіночий рід до розві́дник (військовослужбовець, що веде розвідку).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗВІ́ДНИЦЯ, і, ж. Жін. до розві́дник 1, 3, 4. Яринка '
                                                               'після нашої втечі [з концтабору] була партизанською '
                                                               'зв’язковою і розвідницею (Коз., Гарячі руки, 1960, '
                                                               '109); Незвичайними не лише своєю красою здавалися її '
                                                               'темно-карі очі, в глибині яких то спалахували, то '
                                                               'пригасали білі іскорки. Це були очі людини, якій треба '
                                                               'і яка вміє все бачити й помічати, все карбувати в '
                                                               'своїй пам’яті, очі розвідниці (Жур., Вел. розмова, '
                                                               '1955, 92).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'розвідни́ця',
                 'short_label': 'фахівчиня з розводки пилок (техн.) (C1)',
                 'gloss': 'female saw-tooth setter (operator setting saw teeth in woodworking)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzwʲidˈnɪt͡sʲɐ]'},
                 'stress': {'form': 'розвідни́ця', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розвідниця'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'жіночий',
                                             'animacy': 'animate',
                                             'cases': {'називний': {'singular': 'розвідни́ця'},
                                                       'родовий': {'singular': 'розвідни́ці'},
                                                       'давальний': {'singular': 'розвідни́ці'},
                                                       'знахідний': {'singular': 'розвідни́цю'},
                                                       'орудний': {'singular': 'розвідни́цею'},
                                                       'місцевий': {'singular': 'розвідни́ці'},
                                                       'кличний': {'singular': 'розвідни́це'}}}},
                 'distinction_note': 'Означає робітницю, фахівчиню з розведення зубців пилки (спеціальний технічний '
                                     'термін від «розводити пилку»). Наголос падає на суфікс: розвідни́ця.',
                 'meaning': {'definitions': ['Жіночий рід до розвідни́к (робітниця, фахівчиня з розведення зубців '
                                             'пилки).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗВІДНИ́ЦЯ, і, ж. Жін. до розвідни́к.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'розкидання': [{'headword': 'розки́дання',
                 'short_label': 'дія за знач. розки́дати (швидке або одноразове порозкидання, док.)',
                 'gloss': 'scattering, tossing aside once or rapidly (verbal noun, perf.)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzˈkɪdɐnʲːɐ]'},
                 'stress': {'form': 'розки́дання', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розкидання'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'середній',
                                             'animacy': 'inanimate',
                                             'cases': {'називний': {'singular': 'розки́дання'},
                                                       'родовий': {'singular': 'розки́дання'},
                                                       'давальний': {'singular': 'розки́данню'},
                                                       'знахідний': {'singular': 'розки́дання'},
                                                       'орудний': {'singular': 'розки́данням'},
                                                       'місцевий': {'singular': 'розки́данні'},
                                                       'кличний': {'singular': 'розки́дання'}}}},
                 'distinction_note': 'Віддієслівний іменник від доконаного «розки́дати» (розкидати речі в безладді за '
                                     'один захід). Не плутати з регулярним сільськогосподарським процесом '
                                     '«розкида́ння».',
                 'meaning': {'definitions': ['Дія за значенням розки́дати (швидко або за один раз порозкидати; '
                                             'доконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗКИ́ДАННЯ, я, с. Дія за знач. розки́дати¹.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'розкида́ння',
                 'short_label': 'дія за знач. розкида́ти (регулярне розкидання добрив, сіна, недок.)',
                 'gloss': 'broadcasting, spreading, dispersing regularly (verbal noun, imperf.)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzkɪˈdɑnʲːɐ]'},
                 'stress': {'form': 'розкида́ння', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розкидання'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'середній',
                                             'animacy': 'inanimate',
                                             'cases': {'називний': {'singular': 'розкида́ння'},
                                                       'родовий': {'singular': 'розкида́ння'},
                                                       'давальний': {'singular': 'розкида́нню'},
                                                       'знахідний': {'singular': 'розкида́ння'},
                                                       'орудний': {'singular': 'розкида́нням'},
                                                       'місцевий': {'singular': 'розкида́нні'},
                                                       'кличний': {'singular': 'розкида́ння'}}}},
                 'distinction_note': 'Віддієслівний іменник від недоконаного «розкида́ти» (процес розкидання гною '
                                     'гноєрозкидачем, розкидання каміння чи піску). Не плутати з однократним актом '
                                     '«розки́дання».',
                 'meaning': {'definitions': ['Дія за значенням розкида́ти (регулярно кидати в різні боки; недоконаний '
                                             'вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗКИДА́ННЯ, я, с. Дія за знач. розкида́ти¹. Для '
                                                               'розкидання куп придбали роторний гноєрозкидач, який '
                                                               'працює з трактором ДТ-54 (Хлібороб Укр., 8, 1965, 18); '
                                                               'Необхідно вижити розкидання сил і розпорошення уваги '
                                                               'спілкових організацій (Компартія України в резол. і '
                                                               'рішен.., 1958, 194).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'розпаювати': [{'headword': 'розпа́ювати',
                 'short_label': "роз'єднувати спаяне нагріванням, розплавляти спайку (недок.)",
                 'gloss': 'unsolder, melt apart soldered parts (imperf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzˈpɑjʊwɐtɪ]'},
                 'stress': {'form': 'розпа́ювати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розпаювати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Технічний термін від «паяти»: розпаювати шов паяльником (недок. вид, док. '
                                     '«розпаяти»). Не плутати з розподілом часток майна «розпаюва́ти».',
                 'meaning': {'definitions': ['Роз’єднувати, розплавляти щось на місці спаювання (недоконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗПА́ЮВАТИ, юю, юєш, недок., РОЗПАЯ́ТИ, я́ю, я́єш, '
                                                               'док., перех. Роз’єднувати, розплавляти щось на місці '
                                                               'спаювання.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'розпаюва́ти',
                 'short_label': 'поділити на пайки, частки або паї між учасниками (док., розм.)',
                 'gloss': 'allot, parcel out into shares/shares among partners (colloq., perf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzpɐjʊˈwɑtɪ]'},
                 'stress': {'form': 'розпаюва́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розпаювати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                 'distinction_note': 'Походить від іменника «пай»: розділити майно, землю або прибутки на частки між '
                                     'пайовиками (док. вид). Не плутати з технічним паянням «розпа́ювати».',
                 'meaning': {'definitions': ['Поділити на пайки, частини між учасниками (доконаний вид; розм.).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗПАЮВА́ТИ, ю́ю, ю́єш, док., перех., розм. Поділити '
                                                               'на пайки, частини.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'розповзатися': [{'headword': 'розпо́взатися',
                   'short_label': 'почати багато або довго повзати (док., розм.)',
                   'gloss': 'start crawling around extensively (colloq., perf.)',
                   'pos': 'verb',
                   'cefr': 'B2',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[rɔzˈpɔu̯zɐtɪsʲɐ]'},
                   'stress': {'form': 'розпо́взатися',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/розповзатися'},
                   'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                   'distinction_note': 'Означає розійтися у повзанні, почати довго й інтенсивно повзати («малеча '
                                       'розповзалася по всій кімнаті»; док. вид). Не плутати з розлізанням урізнобіч '
                                       '«розповза́тися».',
                   'meaning': {'definitions': ['Почати багато або довго повзати (доконаний вид; розм.).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'РОЗПО́ВЗАТИСЯ, аюся, аєшся, док., розм. Почати '
                                                                 'багато або довго повзати.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None},
                  {'headword': 'розповза́тися',
                   'short_label': 'відповзати в різні боки або розлазитися по швах чи тканині (недок.)',
                   'gloss': 'crawl apart in all directions; unravel at seams (imperf.)',
                   'pos': 'verb',
                   'cefr': 'B1',
                   'heritage_status': {'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                   'pronunciation': {'ipa': '[rɔzpɔu̯ˈzɑtɪsʲɐ]'},
                   'stress': {'form': 'розповза́тися',
                              'source': 'ВТС',
                              'url': 'https://slovnyk.me/dict/vts/розповзатися'},
                   'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                   'distinction_note': 'Означає розповзатися істотам урізнобіч («вужі розповзаються») або тканині '
                                       'рватися по швах від старості (недок. вид, док. «розповзтися»). Не плутати з '
                                       'дією «розпо́взатися».',
                   'meaning': {'definitions': ['Відповзати в різні боки (про багатьох); розлазитися, рватися по швах '
                                               '(недоконаний вид).'],
                               'source': 'ВТС'},
                   'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'РОЗПОВЗА́ТИСЯ, а́ється, недок., РОЗПОВЗТИ́СЯ, '
                                                                 'зе́ться, док. 1. Відповзати в різні боки (про '
                                                                 'кількох або багатьох людей, тварин, комах); '
                                                                 'розлазитися. Автомашини спинилися, з них '
                                                                 'вихоплювалися люди і розповзалися по кюветах (Минко, '
                                                                 'Повна чаша, 1950, 213); // Повільно розходитися, '
                                                                 'роз’їжджатися в різні боки, місця; переставати бути '
                                                                 'разом. Два бронетранспортери вже горіли на подвір’ї, '
                                                                 'інші загули моторами, розповзаючись у темноту '
                                                                 '(Гончар, III, 1956,156); Розтанув і жіночий гурт. '
                                                                 'Поодинці, парами розповзалися присоромлені, '
                                                                 'розгублені молодиці й бабусі (Речм., Весн. грози, '
                                                                 '196І, 107); // Повільно поширюючись, охоплювати '
                                                                 'більший простір (про туман, хмари, дим і т. ін.). '
                                                                 'Туман розповзався нерівними хвилястими кучугурами '
                                                                 '(Коз., Сальвія, 1959, 107); Хмари розповзлися по '
                                                                 'небу сірою запоною (Ткач, Арена, 1960, 52); '
                                                                 '*Образно. Виростало містечко, розповзаючись по '
                                                                 'смітниках, городах та високих узгір’ях (Досв., '
                                                                 'Вибр., 1959, 298); // перех. Ширше розходитися по '
                                                                 'поверхні чого-небудь. Рум’янець розповзається до '
                                                                 'скронь і підборіддя, заливає повне обличчя '
                                                                 '(Стельмах, I, 1962, 312); // Поступово зникати, '
                                                                 'розходячись, розсіваючись у повітрі, в просторі (про '
                                                                 'туман, хмари, дим і т. ін.). Хмари розповзлися — '
                                                                 'виглянуло сонечко (Горд., Дівчина.., 1954, 150); // '
                                                                 'Розростаючись, стелитися по поверхні чого-небудь '
                                                                 '(про рослини або їх частини). Бадилля розповзалось '
                                                                 'скрізь, мов вогняні хробаки (Коцюб., І, 1955, 346); '
                                                                 'Коріння старезних дерев розповзлося по вогкій землі '
                                                                 'й тісно плутається на стежках (Козл., Пов. і опов., '
                                                                 '1949, 212); // перен. Ставати широко відомим (про '
                                                                 'чутки, новини і т. ін.); розголошуватися. Всіляко '
                                                                 'розповзався поголос. Заговорили серед робітників про '
                                                                 'те, що завод виробляє.. зброю (Рибак, Час.., 1960, '
                                                                 '95); Коли розповзлася по набережній несподівана '
                                                                 'чутка, ніхто не міг сказати, звідкіля вона '
                                                                 'народилась (Панч, І, 1956, 48). 2. Розпливатися по '
                                                                 'поверхні чого-небудь (про щось рідке). Палаюча '
                                                                 'рідина розповзалася у всі боки (Ткач, Крута хвиля, '
                                                                 '1954, 230); // Розтікаючись, заливати який-небудь '
                                                                 'простір, поверхню чого-небудь. *Образно. На '
                                                                 'темно-синьому килимі лісів, поміж потемнілою глицею '
                                                                 'розповзлись, розлилися жовті, оранжеві, '
                                                                 'вогненно-руді озера (Коз., Сальвія, 1959, 104); // '
                                                                 'Входячи, всмоктуючись у папір, тканину і т. ін., '
                                                                 'утворювати патьоки, плями, залишати сліди (про '
                                                                 'чорнило, фарбу і т. ін.). При кресленні вживають '
                                                                 'спеціальний креслярський папір. Цей папір.. можна '
                                                                 'підчищати ножем і гумкою, туш на ньому не '
                                                                 'розповзається (Кресл., 1956, 19); // Від вологи '
                                                                 'втрачати виразність, чіткість форм (про що-небудь '
                                                                 'написане або намальоване). Це була записка. Від роси '
                                                                 'вона розмокла, і літери, написані хімічним олівцем, '
                                                                 'розповзлися в сині плями (Панч, В дорозі, 1959, 90); '
                                                                 '// Осуватися в різні боки (про грунт). — Мури оті '
                                                                 'нащо? То їх спеціально зоставляємо між траншеями, '
                                                                 'щоб грунт на сторони не розповзався… (Гончар, '
                                                                 'Тронка, 1963, 190); Могила, колись висока й широка, '
                                                                 'тепер осіла і розповзлася (Тют., Вир, 1964, 201); // '
                                                                 'перен. Поширюватися, заповнюючи собою навколишній '
                                                                 'простір (про звуки, запахи і т. ін.). Тиша '
                                                                 'розповзалась серед пітьми, як туман, і поглинала все '
                                                                 '(Ю. Бедзик, Полки.., 1959, 188). Усмі́шка '
                                                                 '(по́смішка) розповза́ється (розповзла́ся) на '
                                                                 'обли́ччі (по обли́ччю) чиєму — те саме, що Усмі́шка '
                                                                 '(по́смішка) розплива́ється (розпливла́ся) на '
                                                                 'обли́ччі (по обли́ччю) ( див. розплива́тися). Вони '
                                                                 'моргали один на одного та показували пальцями на '
                                                                 'Олександру. Погана усмішка розповзалась по їх '
                                                                 'жовтих, з остудою обличчях (Коцюб., І, 1955, 38). 3. '
                                                                 'Розпадатися, розлазитися, втрачаючи форму, цілість. '
                                                                 'Слід пам’ятати, що.. переобварені овочі в маринаді '
                                                                 'розповзаються (Укр. страви, 1957, 416); // розм. '
                                                                 'Рватися, розлазитися від тривалого носіння (про '
                                                                 'одяг, тканини, взуття). Люди, надіючись, що їх скоро '
                                                                 'обмундирують, брали найветхіший одяг, і тепер він '
                                                                 'розповзався на осінніх дощах (Тют., Вир, 1964, 347); '
                                                                 'Рану печінки майже неможливо з’єднати швами. '
                                                                 'Тендітна тканина розповзається, кровить (Наука.., 6, '
                                                                 '1966, 23). 4. перен., розм. Втрачати певність, '
                                                                 'чіткість, ставати аморфними, невизначеними (про '
                                                                 'думки, спогади і т. ін.). Він і заснув тільки під '
                                                                 'ранок. І через безсонну ніч розповзаються думки, і '
                                                                 'тоскно, наче на безлюдді (Сміл., Зустрічі, 1936, '
                                                                 '76). 5. перен., розм. Ставати ширшим від усмішки, '
                                                                 'радощів, доброго настрою і т. ін.; розпливатися. У '
                                                                 'дідуся приємно розповзлось обличчя, і він '
                                                                 'доброзичливо кивнув до юнака головою (Досв., Гюлле, '
                                                                 '1961, 44); Він сміявся.. Пухлі губи розповзлися під '
                                                                 'чорненькими вусиками (Мур., Бук. повість, 1959, '
                                                                 '225). 6. перен., розм. Розходитися в різні боки, '
                                                                 'вести в різні напрямки (про шляхи, дороги, стежки). '
                                                                 'Ми опинилися під темним склепінням високих дубів, де '
                                                                 'вузенькі стежки гадюками розповзались у траві (Панч, '
                                                                 'II, 1956, 412); // Спадати окремими пасмами (про '
                                                                 'волосся); розпадатися, розсипатися. Сама [Клава] ще '
                                                                 'молода, а вся перемучена, сидить, зсутулившись, і по '
                                                                 'плечі розповзається важкий клубок кіс (Гончар, '
                                                                 'Людина.., 1960, 59).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                      'Наведено для лексикографічної прозорості.'},
                   'pre_soviet_witness': None}],
 'розсадний': [{'headword': 'розса́дний',
                'short_label': 'стосовний до вирощування розсади овочів або квітів (агро)',
                'gloss': 'relating to seedlings or nursery plants (agri.)',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[rɔzˈsɑdnɪj]'},
                'stress': {'form': 'розса́дний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розсадний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Прикметник від «розсада»: вирощування культур через розсаду (розсадний спосіб, '
                                    'розсадні помідори). Не плутати з посадковим матеріалом для пересаджування '
                                    '«розсадни́й».',
                'meaning': {'definitions': ['Прикметник до розса́да (вирощування розсади; агро).'], 'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'РОЗСА́ДНИЙ, а, е. Прикм. до розса́да. На Херсонщині '
                                                              'помідори вирощують розсадним і безрозсадним способами '
                                                              '(Хлібороб Укр., 3, 1965, 28); Встановлено, що фосфор '
                                                              'дуже потрібний помідорам у розсадному віці, зокрема при '
                                                              'появі другого листочка (Колг. Укр., 3, 1958, 39); // '
                                                              'Який розводиться за допомогою розсади. Агротехніка '
                                                              'баклажанів має багато спільного з вирощуванням '
                                                              'розсадних помідорів (Овоч. закр. і відкр. грунту, 1957, '
                                                              '181); Розсадні культури.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None},
               {'headword': 'розсадни́й',
                'short_label': 'призначений для розсаджування у ґрунт (с.-г.)',
                'gloss': 'designated for planting out or transplanting (agri.)',
                'pos': 'adj',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[rɔzsɐdˈnɪj]'},
                'stress': {'form': 'розсадни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розсадний'},
                'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                'distinction_note': 'Спеціальний сільськогосподарський термін: призначений для висаджування на '
                                    'постійне місце (розсадний матеріал). Не плутати з вирощуванням розсади '
                                    '«розса́дний».',
                'meaning': {'definitions': ['Призначений для розсаджування (с.-г.).'], 'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'РОЗСАДНИ́Й, а́, е́, с. г. Признач. для розсаджування.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'розсильний': [{'headword': 'розси́льний',
                 'short_label': "кур'єр, службовець для доставки пошти, пакетів і доручень",
                 'gloss': 'courier, messenger, office runner (noun)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzˈsɪlʲnɪj]'},
                 'stress': {'form': 'розси́льний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розсильний'},
                 'morphology': {'pos': 'іменник',
                                'paradigm': {'kind': 'noun',
                                             'gender': 'чоловічий',
                                             'animacy': 'animate',
                                             'cases': {'називний': {'singular': 'розси́льний'},
                                                       'родовий': {'singular': 'розси́льного'},
                                                       'давальний': {'singular': 'розси́льному'},
                                                       'знахідний': {'singular': 'розси́льного'},
                                                       'орудний': {'singular': 'розси́льним'},
                                                       'місцевий': {'singular': 'розси́льному'},
                                                       'кличний': {'singular': 'розси́льний'}}}},
                 'distinction_note': 'Субстантивований іменник чоловічого роду: особа, що розносить пакети, листи чи '
                                     "повістки (кур'єр). Не плутати з реєстраційною книгою «розсильни́й».",
                 'meaning': {'definitions': ['Той, хто розносить за призначенням листи, пакети, виконує службові '
                                             "доручення; кур'єр."],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗСИ́ЛЬНИЙ, ного, ч. Той, хто розносить за '
                                                               'призначенням листи, пакети, виконує різні доручення і '
                                                               'т. ін.; кур’єр. Розсильні військкоматів з жмутками '
                                                               'повісток в руках шугають цієї пізньої години від '
                                                               'будинку до будинку, від під’їзду до під’їзду (Гончар, '
                                                               'Людина.., 1960, 15); Прибіг розсильний і наказав '
                                                               'Чигиринові негайно, разом із взводом, прибути на '
                                                               'подвір’я (Ткач, Крута хвиля, 1956, 65).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'розсильни́й',
                 'short_label': 'призначений для розсилання або реєстрації розсиланих пакетів',
                 'gloss': 'dispatch, delivery, used for recording outgoing items (adj.)',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[rɔzsɪlʲˈnɪj]'},
                 'stress': {'form': 'розсильни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розсильний'},
                 'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                 'distinction_note': 'Прикметник від «розсилати»: призначений для запису відправлених паперів '
                                     "(розсильна книга) або для розсилання. Не плутати з особою кур'єра «розси́льний».",
                 'meaning': {'definitions': ['Який служить для запису пакетів, що розсилаються (про книгу, зошит); '
                                             'призначений для розсилання.'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'РОЗСИЛЬНИ́Й, а́, е́. 1. Який служить для запису '
                                                               'пакетів, що розсилаються з кур’єром (про книгу, '
                                                               'зошит). 2. Признач. для розсилання.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'розсипка': [{'headword': 'ро́зсипка',
               'short_label': 'втрата у вазі сипких товарів при зважуванні чи пересипанні (розм.)',
               'gloss': 'spillage loss of bulk commodities during transit/weighing (colloq.)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ˈrɔzsɪpkɐ]'},
               'stress': {'form': 'ро́зсипка', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/розсипка'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'ро́зсипка'},
                                                     'родовий': {'singular': 'ро́зсипки'},
                                                     'давальний': {'singular': 'ро́зсипці'},
                                                     'знахідний': {'singular': 'ро́зсипку'},
                                                     'орудний': {'singular': 'ро́зсипкою'},
                                                     'місцевий': {'singular': 'ро́зсипці'},
                                                     'кличний': {'singular': 'ро́зсипко'}}}},
               'distinction_note': 'Торговельне розмовне поняття: природна втрата у вазі сипкого товару (цукру, '
                                   'борошна, зерна) через розсипання. Не плутати з самою дією розсипання «розси́пка».',
               'meaning': {'definitions': ['Втрата у вазі сипких товарів (розм.).'], 'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'РО́ЗСИПКА, и, ж., розм. Втрата у вазі сипких товарів. '
                                                             'Переважили. — Скільки? — 620 [пудів цукру]! Але справді '
                                                             '600, бо ті двадцять із усушки.. і з розсипки набрались… '
                                                             '(Вишня, І, 1956, 141).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'розси́пка',
               'short_label': 'дія за значенням розсипати або сипкий стан; в розсипку (розм.)',
               'gloss': 'act of scattering or scattered/loose state; en vrac (colloq.)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[rɔzˈsɪpkɐ]'},
               'stress': {'form': 'розси́пка',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/розсипка'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'жіночий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'розси́пка'},
                                                     'родовий': {'singular': 'розси́пки'},
                                                     'давальний': {'singular': 'розси́пці'},
                                                     'знахідний': {'singular': 'розси́пку'},
                                                     'орудний': {'singular': 'розси́пкою'},
                                                     'місцевий': {'singular': 'розси́пці'},
                                                     'кличний': {'singular': 'розси́пко'}}}},
               'distinction_note': 'Позначає сам процес розсипання або вживання у виразі «в розсипку» (врозсип, '
                                   'урозтіч). Не плутати з товарною недостачею ваги «ро́зсипка».',
               'meaning': {'definitions': ['Те саме, що розсипа́ння; стан розсипаного (розм.).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'РОЗСИ́ПКА, и, ж., розм. Те саме, що розсипа́ння.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Розсипка, -ки, ж. В розсипку. В разсыпную. В розсипку кінних '
                                               'роспустивши, сам як опарений кричав. Котл. Ен.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}}],
 'романець': [{'headword': 'рома́нець',
               'short_label': 'зневажливе до роман (низькопробний бульварний або розважальний твір)',
               'gloss': 'trashy pulp novel, frivolous romance (pejorative, colloq.)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[rɔˈmɑnɛt͡sʲ]'},
               'stress': {'form': 'рома́нець', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/романець'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'чоловічий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'рома́нець'},
                                                     'родовий': {'singular': 'рома́нця'},
                                                     'давальний': {'singular': 'рома́нцю'},
                                                     'знахідний': {'singular': 'рома́нець'},
                                                     'орудний': {'singular': 'рома́нцем'},
                                                     'місцевий': {'singular': 'рома́нці'},
                                                     'кличний': {'singular': 'рома́нцю'}}}},
               'distinction_note': 'Зневажлива назва літературного твору: нікчемний чи легковажний роман («наплодилося '
                                   'таких, що пишуть романці та теревені»). Не плутати з польовою ромашкою '
                                   '«романе́ць».',
               'meaning': {'definitions': ['Зневажливе до роман (легковажний або другосортний літературний твір).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'РОМА́НЕЦЬ, нця, ч., зневажл. Те само, що роман¹. — '
                                                             'Наплодилося до ката у вас таких, що пишуть повісті та '
                                                             'романці і усякі теревені (Кв.-Осн., II, 1956, 249).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'романе́ць',
               'short_label': 'пестливе до роман (дика ромашка, лікарська трава або квітка)',
               'gloss': 'wild chamomile, ox-eye daisy or feverfew (botanical, folk)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[rɔmɐˈnɛt͡sʲ]'},
               'stress': {'form': 'романе́ць',
                          'source': 'Грінченко (1907) / ВТС',
                          'url': 'https://slovnyk.me/dict/vts/романець'},
               'morphology': {'pos': 'іменник',
                              'paradigm': {'kind': 'noun',
                                           'gender': 'чоловічий',
                                           'animacy': 'inanimate',
                                           'cases': {'називний': {'singular': 'романе́ць'},
                                                     'родовий': {'singular': 'романця́'},
                                                     'давальний': {'singular': 'романцю́'},
                                                     'знахідний': {'singular': 'романе́ць'},
                                                     'орудний': {'singular': 'романце́м'},
                                                     'місцевий': {'singular': 'романці́'},
                                                     'кличний': {'singular': 'романцю́'}}}},
               'distinction_note': 'Ботанічна народна назва: ромашка лікарська чи пижмо («росте зіллячко '
                                   'романець...»). Не плутати з літературним романом «рома́нець».',
               'meaning': {'definitions': ['Пестливе до рома́н (польова квітка, ромашка або пижмо; рідко).'],
                           'source': 'Грінченко (1907) / ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'РОМАНЕ́ЦЬ, нця́, ч., рідко. Пестл. до рома́н². Росте '
                                                             'зіллячко романець… Кращий парубок, як вдовець (Укр. нар. '
                                                             'пісні, 2, 1965, 324).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                      'quote': 'Романець, -нця, м. 1) Ум. от роман. 2) Раст. Chrysanthemum corymbosum. '
                                               'Вх. Пч. II. 30.',
                                      'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                         'Грінченком в умовах дії антиукраїнських імперських указів '
                                                         '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                         'р.).'}}],
 'сажковий': [{'headword': 'са́жковий',
               'short_label': 'стосовний до хвороби злаків «сажка» або паразитичних сажкових грибів',
               'gloss': 'smut-fungal, relating to cereal smut infection (phytopath.)',
               'pos': 'adj',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[ˈsɑʒkɔwɪj]'},
               'stress': {'form': 'са́жковий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сажковий'},
               'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
               'distinction_note': 'Фітопатологічний термін від «сажка» (хвороба хлібних злаків, викликана '
                                   'паразитичними грибами: сажкові спори, сажкові гриби). Не плутати з сажем для '
                                   'худоби «сажко́вий».',
               'meaning': {'definitions': ['Прикметник до са́жка (хвороба злаків); сажкові гриби.'], 'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'СА́ЖКОВИЙ, а, е. 1. Прикм. до са́жка. Сажкову масу, що '
                                                             'утворюється замість зерен або волоті, спочатку вкриває '
                                                             'біла оболонка, яка згодом тріскається (Шкідн. і хвор.. '
                                                             'рослин, 1956, 127); Сажкові гриби. 2. у знач. ім. '
                                                             'са́жкові, вих, мн. Рід нижчих спорових грибів-паразитів, '
                                                             'що стимулюють появу сажки на злакових рослинах. Сажкові '
                                                             '— дуже поширені паразитні гриби, які особливо часто '
                                                             'пошкоджують зернові культури (Практ. з систем. та морф. '
                                                             'рослин, 1955, 52).',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None},
              {'headword': 'сажко́вий',
               'short_label': 'стосовний до сажка (клітки або загороди для відгодівлі птиці чи свиней)',
               'gloss': 'relating to a fattening coop or pen for fowl/swine',
               'pos': 'adj',
               'cefr': 'B2',
               'heritage_status': {'classification': 'standard',
                                   'is_russianism': False,
                                   'russian_shadow': False,
                                   'vesum_attested': True},
               'pronunciation': {'ipa': '[sɐʒˈkɔwɪj]'},
               'stress': {'form': 'сажко́вий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сажковий'},
               'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
               'distinction_note': 'Прикметник від «сажо́к» (клітка під похилим дахом для відгодовування гусей, курей '
                                   'чи підсвинків). Не плутати з грибковим захворюванням рослин «са́жковий».',
               'meaning': {'definitions': ['Прикметник до сажо́к (клітка чи загорода для відгодівлі свійських тварин '
                                           'чи птиці).'],
                           'source': 'ВТС'},
               'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                               'definition': 'САЖКО́ВИЙ, а, е. Прикм. до сажо́к.',
                                               'sovietization_risk': 0,
                                               'keywords': [],
                                               'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                  'для лексикографічної прозорості.'},
               'pre_soviet_witness': None}],
 'сапання': [{'headword': 'са́пання',
              'short_label': 'важке переривчасте сопіння, шумне дихання від утоми чи вві сні',
              'gloss': 'heavy wheezing, snorting or laboured breathing',
              'pos': 'noun',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈsɑpɐnʲːɐ]'},
              'stress': {'form': 'са́пання', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сапання'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'середній',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'са́пання'},
                                                    'родовий': {'singular': 'са́пання'},
                                                    'давальний': {'singular': 'са́панню'},
                                                    'знахідний': {'singular': 'са́пання'},
                                                    'орудний': {'singular': 'са́панням'},
                                                    'місцевий': {'singular': 'са́панні'},
                                                    'кличний': {'singular': 'са́пання'}}}},
              'distinction_note': 'Звукове фізіологічне явище: важке, шумне дихання носом або сопіння сплячої людини '
                                  "(«сонне сапання, важке сапання»). Не плутати з прополюванням бур'янів «сапа́ння».",
              'meaning': {'definitions': ['Дія за значенням са́пати (сопіти) і звуки, утворювані цією дією; важке '
                                          'дихання.'],
                          'source': 'ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'СА́ПАННЯ, я, с. Дія за знач. са́пати і звуки, утворювані '
                                                            'цією дією. Кругом тихо було,.. тілько сонне сапання '
                                                            'служниці чути було з-за печі (Фр., V, 1951, 407); Нараз '
                                                            'до його слуху долетіло з боку омшаника важке сапання і '
                                                            'глухий гупіт (Кол., Терен.., 1959, 109); *У порівн. Гомін '
                                                            'хвиль перейшов у бухання. Спочатку глухе, як важке '
                                                            'сапання (Коцюб., І, 1955, 391).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': None},
             {'headword': 'сапа́ння',
              'short_label': "прополювання сапою посівів та городніх культур від бур'янів",
              'gloss': 'hoeing, weeding with a hoe',
              'pos': 'noun',
              'cefr': 'B1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[sɐˈpɑnʲːɐ]'},
              'stress': {'form': 'сапа́ння',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/сапання'},
              'morphology': {'pos': 'іменник',
                             'paradigm': {'kind': 'noun',
                                          'gender': 'середній',
                                          'animacy': 'inanimate',
                                          'cases': {'називний': {'singular': 'сапа́ння'},
                                                    'родовий': {'singular': 'сапа́ння'},
                                                    'давальний': {'singular': 'сапа́нню'},
                                                    'знахідний': {'singular': 'сапа́ння'},
                                                    'орудний': {'singular': 'сапа́нням'},
                                                    'місцевий': {'singular': 'сапа́нні'},
                                                    'кличний': {'singular': 'сапа́ння'}}}},
              'distinction_note': "Сільськогосподарська праця: обробіток міжрядь сапою для знищення бур'янів («ручне "
                                  'сапання буряків»). Не плутати зі звуком сопіння «са́пання».',
              'meaning': {'definitions': ["Дія за значенням сапа́ти (обробляти сапою, знищуючи бур'яни)."],
                          'source': 'Грінченко (1907) / ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'САПА́ННЯ, я, с. 1. Дія за знач. сапа́ти. Захопившись '
                                                            'сапанням, Тетяна незчулася, як опинилась під зливою '
                                                            '(Добр., Тече річка.., 1961, 94); Найбільш трудомісткою '
                                                            'операцією, як відомо, раніше було ручне сапання. '
                                                            'Механізований міжрядний обробіток звільнив людей від цієї '
                                                            'важкої роботи (Рад. Укр., 22.III 1961, 2). 2. Пора, '
                                                            'період, коли найінтенсивніше сапають. — Дасте мені, куме '
                                                            'Семене, плуга? Я вам відроблю в сапання (Март., Тв., '
                                                            '1954, 75).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Сапання, -ня, с. Полотье.',
                                     'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                        'Грінченком в умовах дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                        'р.).'}}],
 'свататися': [{'headword': 'сва́татися',
                'short_label': 'звертатися з пропозицією одруження через старостів чи особисто (недок.)',
                'gloss': 'court, propose marriage, ask for a hand via matchmakers (imperf.)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[ˈswɑtɐtɪsʲɐ]'},
                'stress': {'form': 'сва́татися',
                           'source': 'Грінченко (1907) / ВТС',
                           'url': 'https://slovnyk.me/dict/vts/свататися'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': 'Традиційний шлюбний обряд: просити руки дівчини через старостів («приїхав до тебе '
                                    'свататись»; недок. вид). Не плутати з підтриманням свояцтва батьками '
                                    '«свата́тися».',
                'meaning': {'definitions': ['Звертатися до батьків дівчини через старостів, прохаючи згоди на '
                                            'одруження (недоконаний вид).'],
                            'source': 'Грінченко (1907) / ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'СВА́ТАТИСЯ, аюся, аєшся, недок. Звертатися до батьків '
                                                              'дівчини, звичайно через старостів або взагалі через '
                                                              'посередників, прохаючи дати згоду на одруження з їхньою '
                                                              'дочкою. — А що, дядьку,— питає царевич,— де твої дочки? '
                                                              'Я приїхав до тебе свататись (Укр.. казки.., 1951, 226); '
                                                              '//Самому пропонувати себе в чоловіки дівчині, жінці. '
                                                              'Щоб закріпить свою любов, Петро, закінчивши роботу, До '
                                                              'Галі свататись пішов (С. Ол., Вибр., 1957, 318).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'Свататися, -таюся, -єшся, гл. 1) Свататься. Тільки що задумаєш '
                                                'свататись, то й станеш зараз брехати: без брехні пі жоден чоловік не '
                                                'сватався. Ном. № 8961. В нижеследующем значеніи с измененным удар.: '
                                                'свататися: 2) Делаться по отношенію друг к другу сватами в значеніи '
                                                'сват 1 и 2. Cм. еще свахатися.',
                                       'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                          'Грінченком в умовах дії антиукраїнських імперських указів '
                                                          '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                          'р.).'}},
               {'headword': 'свата́тися',
                'short_label': "родичатися, ставати сватами / підтримувати зв'язки родинами (недок.)",
                'gloss': 'foster relations between in-law families, become related by marriage (imperf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[swɐˈtɑtɪsʲɐ]'},
                'stress': {'form': 'свата́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/свататися'},
                'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': "Означає встановлювати зв'язки свояцтва, підтримувати добрі взаємини між родинами "
                                    'подружжя («з кумом не сватайся, з паном не братайся»; недок. вид). Не плутати з '
                                    'залицянням нареченого «сва́татися».',
                'meaning': {'definitions': ['Ставати сватами, підтримувати стосунки із сватами (недоконаний вид).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'СВАТА́ТИСЯ, а́юся, а́єшся, недок. Ставати сватами ( '
                                                              'див. сват¹ 2); підтримувати добрі стосунки із сватами. '
                                                              'З кумом не сватайся, з паном не братайся (Укр.. '
                                                              'присл.., 1963, 107).',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}],
 'сипнути': [{'headword': 'си́пнути',
              'short_label': 'робитися сиплим, втрачати дзвінкість, починати сипіти (недок.)',
              'gloss': 'grow hoarse, become husky or wheezy (imperf.)',
              'pos': 'verb',
              'cefr': 'B2',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[ˈsɪpnʊtɪ]'},
              'stress': {'form': 'си́пнути', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сипнути'},
              'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
              'distinction_note': 'Позначає зміну голосу: ставати сиплим через застуду чи втому (недок. вид від '
                                  'сипіти). Не плутати з однократним висипанням зерна «сипну́ти».',
              'meaning': {'definitions': ['Ставати, робитися сиплим; починати сипіти (недоконаний вид).'],
                          'source': 'ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'СИ́ПНУТИ, ну, не́ш, недок. Ставати, робитися сиплим; '
                                                            'починати сипіти.',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': None},
             {'headword': 'сипну́ти',
              'short_label': 'однократне до сипати (кинути або висипати жменю, сипнути зерна; док.)',
              'gloss': 'scatter, sprinkle or pour out once (grain, seeds); surge out (perf.)',
              'pos': 'verb',
              'cefr': 'B1',
              'heritage_status': {'classification': 'standard',
                                  'is_russianism': False,
                                  'russian_shadow': False,
                                  'vesum_attested': True},
              'pronunciation': {'ipa': '[sɪpˈnutɪ]'},
              'stress': {'form': 'сипну́ти',
                         'source': 'Грінченко (1907) / ВТС',
                         'url': 'https://slovnyk.me/dict/vts/сипнути'},
              'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
              'distinction_note': 'Однократна дія від «сипати»: сипнути перцю в борщ, сипнути маку або вибігти юрбою '
                                  '(«от і братія сипнула»; док. вид). Не плутати з хрипотою в голосі «си́пнути».',
              'meaning': {'definitions': ['Однократне до си́пати (посипати швидко або насипати трохи; доконаний вид).'],
                          'source': 'Грінченко (1907) / ВТС'},
              'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                              'definition': 'СИПНУ́ТИ, ну́, не́ш, док. 1. перех. і неперех. Однокр. до '
                                                            'си́пати 1, 4, 6-8. — Одчинила я курник, сипнула зерна і '
                                                            'почала кликати курей (Мирний, І, 1954, 237); Сипнувши в '
                                                            'казанок пучку тонко змеленого перцю, добрі люди вечеряли '
                                                            'смачно (Ільч., Козацьк. роду.., 1958, 71); Іде дорогою, '
                                                            'йде, аж тут від лісу як не зашумить дерев’я [дерева], як '
                                                            'не сипне Якимові вітер цілими пригорщами пороху в очі '
                                                            '(Ков., Світ.., 1960, 10); Дуб.. трусонув золотою гривою, '
                                                            'густо сипнув жолудями — тугими, теплими (Цюпа, '
                                                            'Назустріч.., 1958, 143); Вже ранішнє сонце сипнуло '
                                                            'сріблом, Пригріло рибалок (Шер., Дорога.., 1957, 106); '
                                                            'Виходить дівчина із хати Води в криниці набирати, .. А '
                                                            'він [жайворонок] сипне їй переливів (Мал., Запов. '
                                                            'джерело, 1959, 68); Сипнув міномет!.. Білий снігу папір '
                                                            'Покрився розривами мін (Нех., Хто сіє вітер, 1959, 164); '
                                                            'Він належав до того типу чоловіків, яким природа щедро '
                                                            'сипнула своїх дарів (Рад. Укр., 6.II 1972,4); // безос. '
                                                            'Чую — як загуде в грубі, як сипне, війне снігом у вікна — '
                                                            'зразу стемніло (Вас., II, 1959, 315). ◊ Мов (на́че, як і '
                                                            'т. ін.) хто сипну́в [гаря́чого] при́ску ([гаря́чим] '
                                                            'при́ском) див. при́сок; Моро́зом сипну́ло [за (по́за) '
                                                            'спи́ною (шкі́рою)] у кого, безос.; Мура́шки сипну́ли по '
                                                            'спи́ні (по ті́лу, по шкі́рі) у кого — кого-небудь охопило '
                                                            'неприємне відчуття холоду від страху, несподіваного, '
                                                            'сильного переляку, глибокого душевного переживання і т. '
                                                            'ін. Страшно Петрові стало. Щось перехопило дух, серце '
                                                            'застукало в грудях. Він зупинився, став прислухатись. За '
                                                            'спиною аж морозом сипнуло (Гр., І, 1963, 255); Серце його '
                                                            'мов хто у жмені здавив; поза спиною сипнуло морозом '
                                                            '(Мирний, І, 1954, 320); Недокус посміхався, а в мене '
                                                            'морозом сипнуло поза шкірою (Збан., Малин. дзвін, 1958, '
                                                            '91); У Грицька морозом сипнуло від того Христиного крику '
                                                            '(Мирний, III, 1954, 18); — В мене знову по спині сипнули '
                                                            'мурашки (Сміл., Сашко, 1957,196); Сипну́ти грі́шми '
                                                            '(гроши́ма); Сипну́ти зо́лотом (сорокі́вцями) — надмірно, '
                                                            'нерозсудливо витратити гроші. Як сипнув [Іванець] грішми, '
                                                            'так запорожці за ним роєм (П. Куліш, Вибр., 1969, 58); '
                                                            'Вона сипнула тими грішми на єдине в її життю [житті] '
                                                            'свято (Фр., VIII, 1952, 61); Золотом, немов піском, '
                                                            'сипнув Чиновник із калитки по підлозі (Перв., II, 1958, '
                                                            '129); Сипну́в (безос. сипну́ло) жа́ром на кого, кого — '
                                                            'кого-небудь охопило неприємне відчуття від страху, '
                                                            'несподіваного, сильного переляку і т. ін. Улися почутила, '
                                                            'що на неї неначе одразу хтось сипнув жаром: в неї '
                                                            'спинилось серце і перестало кидатись (Н.-Лев., IV, 1956, '
                                                            '339); — Кум Антон так і не з’явився. Від цих слів Івана '
                                                            'жаром сипнуло в обличчя (Чорн., Потік.., 1956, 69); '
                                                            'Сипну́ти наздога́д — натякнути. Вона почувала, що Онися '
                                                            'знов сипнула наздогад на нестатковитих господарів '
                                                            '(Н.-Лев., III, 1956, 178); Як з ла́нтуха сипну́ти див. '
                                                            'ла́нтух; Як (мов, немо́в і т. ін.) [горо́х] з мішка́ '
                                                            'сипну́ти див. мішо́к. 2. неперех. Раптово, із силою '
                                                            'посипатися; почати інтенсивно падати (про що-небудь сипке '
                                                            'або дрібне). Налапав [Петро] мішок, підставив, витяг '
                                                            'свердло. Зерно сипнуло (Гр., І, 1963, 256); Неначе пух '
                                                            'сипкий з небесної перини, Із хмари снігові сипнули '
                                                            'пелюстки (Рильський, Зим. записи, 1964, 92); Надворі '
                                                            'зненацька сипнув дощ — рівний, теплий, рясний (Баш, '
                                                            'Надія, 1960, 183). 3. неперех. Розлетітися, розсипатися, '
                                                            'бризнути в усі боки дрібними частинками (про що-небудь '
                                                            'сипке або дрібне, про велику кількість предметів). Вдарив '
                                                            '[Світо-люб] ще — сипнули іскри, розлетілася.. велетенська '
                                                            'булава! (Забіла, У.. світ, 1960, 154). 4. неперех. '
                                                            'Швидко, разом вийти, вибігти звідкись або піти, побігти '
                                                            'куди-небудь (про багатьох людей). Гуртом сипнули школярі '
                                                            'до класу (Гр., Без хліба, 1958, 11); Натовп колихнувся, '
                                                            'густо зачавкав ногами на багнистому вигоні і .. сипнув до '
                                                            'лісу, урозтіч (Епік, Тв., 1958, 449); Бренькнула.. кобза, '
                                                            'люди сипнули туди, миттю утворилося густе коло (Бурл., О. '
                                                            'Вересай, 1959, 54).',
                                              'sovietization_risk': 0,
                                              'keywords': [],
                                              'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                 'для лексикографічної прозорості.'},
              'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                     'quote': 'Сипнути, -пну, -неш, гл. 1) Однокр. от сипати. Посыпать сразу. Сипне їм '
                                              'маку, — от вони поки визбірають, вона і втече од їх. Грин. II. 25. 2) '
                                              'Высыпать, выйти во множестве. От і братія сипнула. Шевч. Дітвора так і '
                                              'сипнула в сад. МВ. (О. 1862. III. 69).',
                                     'historical_note': 'Автентичне народне мововживання, зафіксоване Борисом '
                                                        'Грінченком в умовах дії антиукраїнських імперських указів '
                                                        '(Валуєвського циркуляра 1863 р. та Емського указу 1876 '
                                                        'р.).'}}],
 'складування': [{'headword': 'скла́дування',
                  'short_label': 'дія за знач. скла́дувати (складати докупи речі або складати вірші, рідко)',
                  'gloss': 'folding, compiling together or composing verses (rare, verbal noun)',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[ˈsklɑdʊwɐnʲːɐ]'},
                  'stress': {'form': 'скла́дування', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/складування'},
                  'morphology': {'pos': 'іменник',
                                 'paradigm': {'kind': 'noun',
                                              'gender': 'середній',
                                              'animacy': 'inanimate',
                                              'cases': {'називний': {'singular': 'скла́дування'},
                                                        'родовий': {'singular': 'скла́дування'},
                                                        'давальний': {'singular': 'скла́дуванню'},
                                                        'знахідний': {'singular': 'скла́дування'},
                                                        'орудний': {'singular': 'скла́дуванням'},
                                                        'місцевий': {'singular': 'скла́дуванні'},
                                                        'кличний': {'singular': 'скла́дування'}}}},
                  'distinction_note': 'Віддієслівний іменник від рідковживаного «скла́дувати» (складання речей або '
                                      'складання віршів). Не плутати зі складською логістикою «складува́ння».',
                  'meaning': {'definitions': ['Дія за значенням скла́дувати (складати щось докупи; рідко).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'СКЛА́ДУВАННЯ, я, с., рідко. Дія за знач. скла́дувати.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None},
                 {'headword': 'складува́ння',
                  'short_label': 'розміщення продукції на складі для тривалого зберігання (спец.)',
                  'gloss': 'warehousing, storage, bulk depot warehousing (verbal noun, spec.)',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': {'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                  'pronunciation': {'ipa': '[sklɐdʊˈwɑnʲːɐ]'},
                  'stress': {'form': 'складува́ння', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/складування'},
                  'morphology': {'pos': 'іменник',
                                 'paradigm': {'kind': 'noun',
                                              'gender': 'середній',
                                              'animacy': 'inanimate',
                                              'cases': {'називний': {'singular': 'складува́ння'},
                                                        'родовий': {'singular': 'складува́ння'},
                                                        'давальний': {'singular': 'складува́нню'},
                                                        'знахідний': {'singular': 'складува́ння'},
                                                        'орудний': {'singular': 'складува́нням'},
                                                        'місцевий': {'singular': 'складува́нні'},
                                                        'кличний': {'singular': 'складува́ння'}}}},
                  'distinction_note': 'Логістичний спеціальний термін: дія за значенням «складува́ти» (розміщення '
                                      'зерна, матеріалів на складі для безпечного зберігання). Не плутати з рідкісним '
                                      'складанням «скла́дування».',
                  'meaning': {'definitions': ['Дія за значенням складува́ти (розміщення на складі для зберігання; '
                                              'спец.).'],
                              'source': 'ВТС'},
                  'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'СКЛАДУВА́ННЯ, я, с., спец. Дія за знач. складува́ти. '
                                                                'Найефективнішим засобом боротьби з самозігріванням '
                                                                'насіння є сушіння його перед складуванням (Екстр. '
                                                                'метод доб. олії.., 1958, 12).',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                     'Наведено для лексикографічної прозорості.'},
                  'pre_soviet_witness': None}],
 'складувати': [{'headword': 'скла́дувати',
                 'short_label': 'складати докупи речі або складати вірші чи пісні (недок., рідко)',
                 'gloss': 'compile, fold together or compose verses (rare, imperf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[ˈsklɑdʊwɐtɪ]'},
                 'stress': {'form': 'скла́дувати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/складувати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Рідковживаний народний варіант до «складати» («складує посаг, які він пісні '
                                     'складував»; недок. вид). Не плутати з розміщенням на складі «складува́ти».',
                 'meaning': {'definitions': ['Те саме, що склада́ти (класти докупи, компонувати або творити пісні; '
                                             'рідко, недоконаний вид).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'СКЛА́ДУВАТИ, ую, уєш, недок., перех., рідко. Те саме, '
                                                               'що склада́ти 1, 3. Повеселішала панночка, клопочеться '
                                                               'своїм посагом.. Сама ганяє, жениха турляє, — купує, '
                                                               'крає, складує… Як у казані кипіло! (Вовчок, I, 1955, '
                                                               '117); Не зітхай так безнадійно, Скорбних уст не '
                                                               'замикай, Рук не складуй ще подвійно, З лану битви не '
                                                               'тікай (Граб., І, 1959, 62); Які він пісні складував і '
                                                               'як їх співав..! (Вовчок, І, 1955, 349).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None},
                {'headword': 'складува́ти',
                 'short_label': 'розміщувати продукцію на складі для тривалого зберігання (недок., спец.)',
                 'gloss': 'warehouse, store products in a depot (spec., imperf.)',
                 'pos': 'verb',
                 'cefr': 'B2',
                 'heritage_status': {'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                 'pronunciation': {'ipa': '[sklɐdʊˈwɑtɪ]'},
                 'stress': {'form': 'складува́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/складувати'},
                 'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                 'distinction_note': 'Спеціальний логістичний термін: розміщувати у складських приміщеннях на '
                                     'зберігання (недок. вид). Не плутати з компонуванням віршів чи речей '
                                     '«скла́дувати».',
                 'meaning': {'definitions': ['Поміщати у склад для зберігання (недоконаний вид; спец.).'],
                             'source': 'ВТС'},
                 'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'СКЛАДУВА́ТИ, у́ю, у́єш, недок., перех., спец. Поміщати '
                                                               'у склад для зберігання.',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                    'Наведено для лексикографічної прозорості.'},
                 'pre_soviet_witness': None}],
 'скликання': [{'headword': 'скли́кання',
                'short_label': 'термін виборного органу / скликання ради (B1)',
                'gloss': 'convocation, assembly term / session of elected body (parliament cohort)',
                'pos': 'noun',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[ˈsklɪkɐnʲːɐ]'},
                'stress': {'form': 'скли́кання', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/скликання'},
                'morphology': {'pos': 'іменник',
                               'paradigm': {'kind': 'noun',
                                            'gender': 'середній',
                                            'animacy': 'inanimate',
                                            'cases': {'називний': {'singular': 'скли́кання',
                                                                   'plural': 'скли́кання'},
                                                      'родовий': {'singular': 'скли́кання',
                                                                  'plural': 'скли́кань'},
                                                      'давальний': {'singular': 'скли́канню',
                                                                    'plural': 'скли́канням'},
                                                      'знахідний': {'singular': 'скли́кання',
                                                                    'plural': 'скли́кання'},
                                                      'орудний': {'singular': 'скли́канням',
                                                                  'plural': 'скли́каннями'},
                                                      'місцевий': {'singular': 'скли́канні',
                                                                   'plural': 'скли́каннях'},
                                                      'кличний': {'singular': 'скли́кання',
                                                                  'plural': 'скли́кання'}}}},
                'distinction_note': 'Позначає виборний орган певного періоду обрання або період його діяльності '
                                    '(наприклад, «парламент девʼятого скликання»), а також доконану дію за значенням '
                                    '«скли́кати».',
                'meaning': {'definitions': ['Виборний орган певного періоду обрання або період його діяльності; дія за '
                                            'знач. скли́кати.'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'СКЛИ́КАННЯ, я, с. Дія за знач. скли́кати. Скликання '
                                                              'пленуму ЦК стало [в 1910 р.] не тільки партійною '
                                                              'необхідністю, воно стало юридичним обов’язком (Ленін, '
                                                              '20, 1971, 45); Члени Президії [Центрального Комітету '
                                                              'КПРС] можуть обиратись, як правило, не більш як на три '
                                                              'скликання підряд (Програма КПРС, 1961, 121); За '
                                                              'скликання об’єднаного засідання Рад голосували всі '
                                                              '(Головко, II, 1957, 465).',
                                                'sovietization_risk': 1,
                                                'keywords': ['ленін', 'кпрс'],
                                                'historical_note': 'СУМ-11 ілюструє слововживання винятково '
                                                                   'комуністично-партійними джерелами (Ленін, Програма '
                                                                   'КПРС).'},
                'pre_soviet_witness': {'witness': 'Грінченко (1907–1909)',
                                       'quote': 'Скликання, -ня, с. Созываніе.',
                                       'source_context': 'Зафіксовано у Словнику української мови Б. Грінченка.'}},
               {'headword': 'склика́ння',
                'short_label': 'збирання, скликання людей на збори/віче (B1)',
                'gloss': 'convening, gathering, action of calling together (people, meeting)',
                'pos': 'noun',
                'cefr': 'B1',
                'heritage_status': {'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
                'pronunciation': {'ipa': '[sklɪˈkanʲːɐ]'},
                'stress': {'form': 'склика́ння', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/скликання'},
                'morphology': {'pos': 'іменник',
                               'paradigm': {'kind': 'noun',
                                            'gender': 'середній',
                                            'animacy': 'inanimate',
                                            'cases': {'називний': {'singular': 'склика́ння',
                                                                   'plural': 'склика́ння'},
                                                      'родовий': {'singular': 'склика́ння',
                                                                  'plural': 'склика́нь'},
                                                      'давальний': {'singular': 'склика́нню',
                                                                    'plural': 'склика́нням'},
                                                      'знахідний': {'singular': 'склика́ння',
                                                                    'plural': 'склика́ння'},
                                                      'орудний': {'singular': 'склика́нням',
                                                                  'plural': 'склика́ннями'},
                                                      'місцевий': {'singular': 'склика́нні',
                                                                   'plural': 'склика́ннях'},
                                                      'кличний': {'singular': 'склика́ння',
                                                                  'plural': 'склика́ння'}}}},
                'distinction_note': 'Позначає тривалий процес або дію за значенням «склика́ти» (збирання, запрошення '
                                    'до сходин, віча чи засідання).',
                'meaning': {'definitions': ['Дія за знач. склика́ти (збирання в одне місце, скликання людей).'],
                            'source': 'ВТС'},
                'soviet_colonization_context': {'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'СКЛИКА́ННЯ, я, с. Дія за знач. склика́ти.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Зафіксовано в радянський період (СУМ-11). Наведено '
                                                                   'для лексикографічної прозорості.'},
                'pre_soviet_witness': None}]}
