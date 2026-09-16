"""Curated heteronym dataset (Batch 12) for Word Atlas (#8039, #4387).

This module defines 32 curated heteronym lemmas (64 distinct variants)
expanding the curated heteronym SSOT from 360 to 392 lemmas.

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

CURATED_HETERONYMS_BATCH_12: dict[str, list[dict[str, Any]]] = {   'бовтнути': [   {   'headword': 'бо́втну́ти',
                        'short_label': 'плеснути по воді або впасти у воду зі сплеском (док.)',
                        'gloss': 'splash in water, fall into water with a splash (perf.)',
                        'pos': 'verb',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[bɔu̯ˈtnutɪ]'},
                        'stress': {   'form': 'бо́втну́ти',
                                      'source': 'ВТС',
                                      'url': 'https://slovnyk.me/dict/vts/бовтнути'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                        'distinction_note': 'Означає плеснути по воді або шубовснути у воду зі сплеском (однокр. до '
                                            'бовтати 1, 2). Не плутати з «бо́втнути» (зненацька бовкнути, сказати щось '
                                            'невпопад).',
                        'meaning': {   'definitions': ['Однократне до бовтати 1, 2; плеснути по воді, впасти у воду.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'БО́ВТНУ́ТИ, бо́втну́, бо́втне́ш, док. 1. '
                                                                         'Однокр. до бовта́ти 2. Бовтнув [Гаєвський] '
                                                                         'ногою по воді (Коцюб., І, 1955, 145) 2. '
                                                                         'Утворити звук, який буває від сплеску води, '
                                                                         'коли в неї щось падає. Вона тільки почула, '
                                                                         'як дитина впала у воду й бовтнула, неначе '
                                                                         'хто кинув у воду камінь (Н.-Лев., III, 1956, '
                                                                         '90). 3. Раптом, важко впасти. Дока так і '
                                                                         'бовтнула в гарячу смолу (Сл. Гр.); — Скакала '
                                                                         'через річку, і всі три міхи ввірвалися і '
                                                                         'бовтнули в воду (Фр., IV, 1950, 77); Вуж '
                                                                         'відлип від гілки, бовтнув у воду (Стельмах, '
                                                                         'Кров людська.., І, 1957, 128). 4. рідко. '
                                                                         'Кинути (раптом, важко). Дідок такий '
                                                                         'плюгавенький, п’яненький та маленький — '
                                                                         'насилу вдержався од спокуси винести [його] '
                                                                         'під руки надвір і бовтнуть у грязь (Вас., '
                                                                         'IV, 1960, 22).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                  'quote': 'Бовтнути, -ну, -неш, гл. 1) Бултыхнуть, упасть в воду. '
                                                           'Левиц. І. 195. Бовтнув, як дурень у воду. Посл. Вона так і '
                                                           'бовтнула в гарячу смолу. ЗОЮР. І. 308. Бовтнуло би тобов у '
                                                           'безодню! (Брань). Фр. Пр. 63. 2) Болтнуть. Язиком бовтне '
                                                           'та не доведе, а по спині є. Ном. № 1122. От і бовтнув '
                                                           'чорзнати що! Н. Вол. у.',
                                                  'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                     'Борисом Грінченком в умовах дії антиукраїнських '
                                                                     'імперських указів (Валуєвського циркуляра 1863 '
                                                                     'р. та Емського указу 1876 р.).'}},
                    {   'headword': 'бо́втнути',
                        'short_label': 'зненацька бовкнути, сказати щось недоречно (док., розм.)',
                        'gloss': 'blurt out, say something unexpectedly or inappropriately (perf., colloq.)',
                        'pos': 'verb',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈbɔu̯tnutɪ]'},
                        'stress': {'form': 'бо́втнути', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/бовтнути'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                        'distinction_note': 'Означає зненацька сказати щось зайве чи необдумане (однокр. до бовтати 3; '
                                            'розм. бовкнути). Не плутати з фізичним сплеском у воді «бо́втну́ти».',
                        'meaning': {   'definitions': ['Однократне до бовтати 3; бовкнути, сказати щось зненацька.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'БО́ВТНУТИ, ну, неш, док., перех. і без '
                                                                         'додатка, розм. Сказати що-небудь, не '
                                                                         'обдумавши, навмання; сказати дурницю; '
                                                                         'бовкнути. Язиком бовтне та не доведе (Номис, '
                                                                         '1864, № 1122); — Може, ти, Льоню, що бовтнув '
                                                                         'про їх при кому? — сказала писарша до брата '
                                                                         '(Н.-Лев., IV, 1956, 136); — Тьфу!.. Що то за '
                                                                         'естетичне, що за гарне слово! Ляпнув! — Ну, '
                                                                         'то нехай тобі буде: бовтнув! (Фр., III, '
                                                                         '1950, 10); Вона глянула на мене заляканими '
                                                                         'очима.. і "Добрий день" … бовтнула стисненим '
                                                                         'голосом (Коб., III, 1956, 27).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'гуконути': [   {   'headword': 'гуко́ну́ти',
                        'short_label': 'голосно крикнути, покликати з силою (док.)',
                        'gloss': 'shout loudly, call out with strength (perf.)',
                        'pos': 'verb',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ɦukɔˈnutɪ]'},
                        'stress': {   'form': 'гуко́ну́ти',
                                      'source': 'ВТС',
                                      'url': 'https://slovnyk.me/dict/vts/гуконути'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                        'distinction_note': 'Означає голосно або з силою крикнути, гукнути когось (однокр. до гукати '
                                            '1, 2). Не плутати з шумовим значенням або вигуками в танці «гукону́ти».',
                        'meaning': {   'definitions': ['Однократне до гукати 1, 2; голосно гукнути, покликати.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ГУКО́НУ́ТИ, ко́ну́, ко́не́ш, док., однокр., '
                                                                         'розм. Підсил. до гу́кну́ти. Аж ось ударили в '
                                                                         'дзвін. Зично та гучно гуконув він на всю '
                                                                         'околицю, оповіщаючи людям про свято (Мирний, '
                                                                         'IV, 1955, 100).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                  'quote': 'ГукОнУти, -ну, -неш, гл. То же, что и гукнУти, но с силой. '
                                                           'Грізно гуконув Грицько. Мир. Пов. І. 116. А чоловік з '
                                                           'борозни: «а куди?» як гуконе! Драг. 15. Гуконула '
                                                           'гаківниця. Мир. ХРВ. 126.',
                                                  'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                     'Борисом Грінченком в умовах дії антиукраїнських '
                                                                     'імперських указів (Валуєвського циркуляра 1863 '
                                                                     'р. та Емського указу 1876 р.).'}},
                    {   'headword': 'гукону́ти',
                        'short_label': 'гучно пролунати, загриміти або крикнути в танці (док., розм.)',
                        'gloss': 'boom, roar, thunder or shout in dance (perf., colloq.)',
                        'pos': 'verb',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ɦukɔˈnutɪ]'},
                        'stress': {'form': 'гукону́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/гуконути'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                        'distinction_note': 'Означає гучно прогриміти, пролунати (про вибух, грім) або весело '
                                            'вигукнути під час танцю (однокр. до гукати 3, 4). Не плутати зі '
                                            'зверненням до когось «гуко́ну́ти».',
                        'meaning': {   'definitions': ['Однократне до гукати 3, 4; гучно загриміти, пролунати.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ГУКОНУ́ТИ, ну́, не́ш, док., однокр., перех. '
                                                                         'і неперех. Підсил. до гукну́ти. Що тепер із '
                                                                         'ним зробилось! Де в біса й сила тая ділась! '
                                                                         'А то було як гуконе (Гл., Вибр., 1957, 41); '
                                                                         '-Вассси-и-лю! —гуконув Івась своїм чистим і '
                                                                         'тонким голосом, аж луна роздалася (Мирний, '
                                                                         'IV, 1955, 14).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'натяжка': [   {   'headword': 'на́тя́жка',
                       'short_label': 'дія з натягання або сила натягування мотузки, тканини тощо',
                       'gloss': 'stretching, tensioning (mechanical action)',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[ˈnɑtʲɑʒkɐ]'},
                       'stress': {'form': 'на́тя́жка', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/натяжка'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'жіночий',
                                                         'cases': {   'називний': {   'singular': 'на́тя́жка',
                                                                                      'plural': 'на́тя́жки'},
                                                                      'родовий': {   'singular': 'на́тя́жки',
                                                                                     'plural': 'на́тя́жок'},
                                                                      'давальний': {   'singular': 'на́тя́жці',
                                                                                       'plural': 'на́тя́жкам'},
                                                                      'знахідний': {   'singular': 'на́тя́жку',
                                                                                       'plural': 'на́тя́жки'},
                                                                      'орудний': {   'singular': 'на́тя́жкою',
                                                                                     'plural': 'на́тя́жками'},
                                                                      'місцевий': {   'singular': 'на́тя́жці',
                                                                                      'plural': 'на́тя́жках'},
                                                                      'кличний': {   'singular': 'на́тя́жко',
                                                                                     'plural': 'на́тя́жки'}}}},
                       'distinction_note': 'Означає фізичну дію натягання дроту, полотна або ступінь їхнього натягу. '
                                           'Не плутати з переносним значенням логічної необґрунтованості «натя́жка».',
                       'meaning': {'definitions': ['Дія за значенням натягати, натягти.'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'НА́ТЯ́ЖКА, и, ж. Неправомірне допущення '
                                                                        'чого-небудь, штучність. Думка про "Слово о '
                                                                        'полку Ігоревім" як про попередника дум XVI— '
                                                                        'XVII ст. спокуслива.. Аналогії з радянською '
                                                                        'поезією в даному випадку, звичайно, можуть '
                                                                        'здатися натяжкою (Від давнини.., І, 1960, '
                                                                        '118); Читач суворий: він ніколи не простить '
                                                                        'письменникові натяжки, фальші, брехні '
                                                                        '(Смолич, Перша книга, 1951, 39).',
                                                          'sovietization_risk': 1,
                                                          'keywords': ['радянськ'],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості; цитує радянську поезію.'},
                       'pre_soviet_witness': None},
                   {   'headword': 'натя́жка',
                       'short_label': 'необґрунтоване твердження, притягнутий за вуха висновок (перен.)',
                       'gloss': 'far-fetched assumption, stretch, strained interpretation (fig.)',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[nɐˈtʲɑʒkɐ]'},
                       'stress': {'form': 'натя́жка', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/натяжка'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'жіночий',
                                                         'cases': {   'називний': {   'singular': 'натя́жка',
                                                                                      'plural': 'натя́жки'},
                                                                      'родовий': {   'singular': 'натя́жки',
                                                                                     'plural': 'натя́жок'},
                                                                      'давальний': {   'singular': 'натя́жці',
                                                                                       'plural': 'натя́жкам'},
                                                                      'знахідний': {   'singular': 'натя́жку',
                                                                                       'plural': 'натя́жки'},
                                                                      'орудний': {   'singular': 'натя́жкою',
                                                                                     'plural': 'натя́жками'},
                                                                      'місцевий': {   'singular': 'натя́жці',
                                                                                      'plural': 'натя́жках'},
                                                                      'кличний': {   'singular': 'натя́жко',
                                                                                     'plural': 'натя́жки'}}}},
                       'distinction_note': 'Переносне значення: штучно притягнуте тлумачення, необґрунтований здогад '
                                           'або перебільшення («твердження з натяжкою»). Не плутати з фізичним '
                                           'натягуванням «на́тя́жка».',
                       'meaning': {   'definitions': ['Необґрунтоване твердження, припущення; натягнутість.'],
                                      'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'НАТЯ́ЖКА, и, ж. Дія і стан за знач. '
                                                                        'натяга́ти¹, натягти́¹ і натяга́тися¹, '
                                                                        'натягти́ся 1. Екіпажі повискакували з люків, '
                                                                        'зосереджено, без команди, ще раз почали '
                                                                        'оглядати машини: перевіряли ходові частини, '
                                                                        'натяжку гусениць, пальці ведучих коліс '
                                                                        '(Стельмах, Вел. рідня, 1951, 647).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None}],
    'недіючий': [   {   'headword': 'неді́ючий',
                        'short_label': 'який перебуває в стані спокою або бездіяльності (калька, :bad)',
                        'gloss': 'inactive, inoperative, dormant (volcano, factory; calque)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'calque',
                                               'is_russianism': True,
                                               'russian_shadow': True,
                                               'vesum_attested': True,
                                               'warning_severity': 'caution',
                                               'calque_warning': {   'standard_alternatives': [   'недієвий',
                                                                                                  'нечинний',
                                                                                                  'непрацюючий']}},
                        'pronunciation': {'ipa': '[nɛˈdʲijut͡ʃɪj]'},
                        'stress': {'form': 'неді́ючий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/недіючий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': "Калька з рос. «недействующий», маркована у ВЕСУМ як :bad. Означає об'єкт, "
                                            'який фактично не працює, законсервований або спить (недіючий вулкан). У '
                                            'сучасній нормі рекомендовано вживати «непрацюючий», «згаслий» або '
                                            '«недієвий». Не плутати з «недію́чий».',
                        'meaning': {'definitions': ['Який не діє, перебуває в стані спокою.'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'НЕДІ́ЮЧИЙ, а, е. Який не діє, не працює в '
                                                                         'даний момент. Леон зауважив, що Завадка '
                                                                         'приглядається до недіючого вентилятора, і '
                                                                         'поквапливо пояснив: — Він електричний '
                                                                         '(Вільде, Сестри.., 1958, 122). Неді́ючий '
                                                                         'вулка́н — вулкан, який не діє, не '
                                                                         'вивергається: згаслий вулкан. В районі міста '
                                                                         'Владиславівки.. розміщений великий, '
                                                                         'складений з висохлої грязі, горб Туш-Оба, що '
                                                                         'являє собою вулканічну побудову недіючого '
                                                                         'вулкана (Геол. Укр., 1959, 657).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'недію́чий',
                        'short_label': 'який утратив юридичну чинність, нечинний (калька, :bad)',
                        'gloss': 'no longer valid, void, inoperative (law, rule; calque, nonstandard)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'calque',
                                               'is_russianism': True,
                                               'russian_shadow': True,
                                               'vesum_attested': True,
                                               'warning_severity': 'caution',
                                               'calque_warning': {'standard_alternatives': ['нечинний', 'недієвий']}},
                        'pronunciation': {'ipa': '[nɛdʲiˈjut͡ʃɪj]'},
                        'stress': {'form': 'недію́чий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/недіючий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Калька з рос. «недействующий», маркована у ВЕСУМ як :bad. Означає '
                                            'нормативний акт, що втратив юридичну силу. У сучасній літературній мові '
                                            'рекомендовано вживати нормативне «нечинний». Не плутати з «неді́ючий».',
                        'meaning': {   'definitions': ['Який утратив чинність (про нормативний акт, закон тощо).'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'НЕДІЮ́ЧИЙ, а, е. Позбавлений активності; '
                                                                         'пасивний. Письменник.. підганяв лінивих, '
                                                                         'будив їх, щоб ніхто не спав, щоб всі '
                                                                         'прокинулись .. Блискавка і грім — це той '
                                                                         'постійний супровід до творчого голосу '
                                                                         'Коцюбинського, без якого голос його був би '
                                                                         'просто ненатуральний, недіючий, неповний '
                                                                         '(Тич., III, 1957, 356).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'обладувати': [   {   'headword': 'обла́дувати',
                          'short_label': 'володіти, порядкувати чим-небудь (арх., недок.)',
                          'gloss': 'possess, hold ownership of, rule or manage (arch., imperf.)',
                          'pos': 'verb',
                          'cefr': 'B2',
                          'heritage_status': {   'classification': 'authentic-archaism',
                                                 'is_russianism': False,
                                                 'russian_shadow': False,
                                                 'vesum_attested': True,
                                                 'warning_severity': 'treasured'},
                          'pronunciation': {'ipa': '[ɔˈblɑduwɐtɪ]'},
                          'stress': {   'form': 'обла́дувати',
                                        'source': 'ВТС',
                                        'url': 'https://slovnyk.me/dict/vts/обладувати'},
                          'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                          'distinction_note': 'Застаріле значення: володіти, порядкувати, управляти чим-небудь («Мій '
                                              'брат буде обладувати полем»). Марковане у ВЕСУМ як :arch. Не плутати з '
                                              '«обла́дува́ти» (спорядити, вирядити в дорогу).',
                          'meaning': {   'definitions': ['Застаріле: володіти, порядкувати, управляти чим-небудь.'],
                                         'source': 'Грінченко'},
                          'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                             'definition': 'ОБЛА́ДУВАТИ, ую, уєш, недок., чим, заст. '
                                                                           'Володіти. Мій брат буде обладувати полем '
                                                                           '(Сл. Гр.); Чим обладуєм ми, те приємніше '
                                                                           'нам; хоч ми й іншого прагнем давно (Др. '
                                                                           'Хмара, Вибр., 1969, 166).',
                                                             'sovietization_risk': 0,
                                                             'keywords': [],
                                                             'historical_note': 'Зафіксовано в радянський період '
                                                                                '(СУМ-11). Наведено для '
                                                                                'лексикографічної прозорості.'},
                          'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                    'quote': 'Обладувати, -дую, -єш, гл. Владеть, обладать. МВ. І. '
                                                             '137. Мій брат буде обладувати полем. Рк. Левиц. '
                                                             'Володимир князь царством всім обладує. Драг. 249.',
                                                    'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                       'Борисом Грінченком в умовах дії '
                                                                       'антиукраїнських імперських указів '
                                                                       '(Валуєвського циркуляра 1863 р. та Емського '
                                                                       'указу 1876 р.).'}},
                      {   'headword': 'обла́дува́ти',
                          'short_label': 'обладнати, спорядити, вирядити в дорогу (арх., док., варіантний наголос)',
                          'gloss': 'equip, fit out, prepare and furnish for a journey (arch., perf.)',
                          'pos': 'verb',
                          'cefr': 'B2',
                          'heritage_status': {   'classification': 'authentic-archaism',
                                                 'is_russianism': False,
                                                 'russian_shadow': False,
                                                 'vesum_attested': True,
                                                 'warning_severity': 'treasured'},
                          'pronunciation': {'ipa': '[ɔblɐduˈwɑtɪ]'},
                          'stress': {   'form': 'обла́дува́ти',
                                        'source': 'ВТС',
                                        'url': 'https://slovnyk.me/dict/vts/обладувати'},
                          'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                          'distinction_note': 'Застаріле значення: спорядити або підготувати до виїзду (вози, коней: '
                                              '«Обладували вози в дорогу»). Марковане у ВЕСУМ як :arch. Не плутати з '
                                              '«обла́дувати» (володіти чим-небудь).',
                          'meaning': {   'definitions': ['Застаріле: обладнати, спорядити, підготувати до виїзду.'],
                                         'source': 'Грінченко'},
                          'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                             'definition': 'ОБЛА́ДУВА́ТИ, у́ю, у́єш, док., перех., '
                                                                           'заст. Обладнати, спорядити. Обладували '
                                                                           'вози в дорогу (Сл. Гр.).',
                                                             'sovietization_risk': 0,
                                                             'keywords': [],
                                                             'historical_note': 'Зафіксовано в радянський період '
                                                                                '(СУМ-11). Наведено для '
                                                                                'лексикографічної прозорості.'},
                          'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                    'quote': 'Обладувати 2, -дУю, -єш, гл. Приготовить, снарядить. '
                                                             'Обладували вози в дорогу.',
                                                    'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                       'Борисом Грінченком в умовах дії '
                                                                       'антиукраїнських імперських указів '
                                                                       '(Валуєвського циркуляра 1863 р. та Емського '
                                                                       'указу 1876 р.).'}}],
    'поливка': [   {   'headword': 'по́ли́вка',
                       'short_label': 'тонка глазур або полива на гончарних чи кулінарних виробах',
                       'gloss': 'glaze, icing (on ceramics or pastry)',
                       'pos': 'noun',
                       'cefr': 'B1',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[ˈpɔlɪu̯kɐ]'},
                       'stress': {'form': 'по́ли́вка', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/поливка'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'жіночий',
                                                         'cases': {   'називний': {   'singular': 'по́ливка',
                                                                                      'plural': 'по́ливки'},
                                                                      'родовий': {   'singular': 'по́ливки',
                                                                                     'plural': 'по́ливок'},
                                                                      'давальний': {   'singular': 'по́ливці',
                                                                                       'plural': 'по́ливкам'},
                                                                      'знахідний': {   'singular': 'по́ливку',
                                                                                       'plural': 'по́ливки'},
                                                                      'орудний': {   'singular': 'по́ливкою',
                                                                                     'plural': 'по́ливками'},
                                                                      'місцевий': {   'singular': 'по́ливці',
                                                                                      'plural': 'по́ливках'},
                                                                      'кличний': {   'singular': 'по́ливко',
                                                                                     'plural': 'по́ливки'}}}},
                       'distinction_note': 'Означає склоподібну або цукрову глазур (поливу) на посуді або випічці. Не '
                                           'плутати з традиційною першою стравою «поли́вка».',
                       'meaning': {'definitions': ['Те саме, що поли́ва (глянсове покриття).'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'ПО́ЛИ́ВКА, и, ж. 1. Рідка приправа, яку '
                                                                        'додають у страву для поліпшення її смаку; '
                                                                        'підлива, соус. Із моєї сипанки смачна страва '
                                                                        'буде, Поливку і маслечко дадуть добрі люди! '
                                                                        '(Гл., Вибр., 1951, 233); [Xуса:] Краще йди '
                                                                        'сама в пекарню і розкажи, як треба готувати '
                                                                        'ту поливку до риби, по-саронськи (Л. Укр., '
                                                                        'III, 1952, 183). 2. діал. Юшка, суп. Я тобі, '
                                                                        'Іванку, курку зарізала на поливку (Томч., '
                                                                        'Жменяки, 1964, 260); Заходить він до кухні, а '
                                                                        'там на столі стоїть страва: по́ливка, м’ясо, '
                                                                        'ще до того й кухоль пива (Калин, Закарп. '
                                                                        'казки, 1955, 60).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None},
                   {   'headword': 'поли́вка',
                       'short_label': 'рідка традиційна страва, юшка або грибний/овочевий суп',
                       'gloss': 'traditional soup, broth, clear vegetable or mushroom soup',
                       'pos': 'noun',
                       'cefr': 'B1',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[pɔˈlɪu̯kɐ]'},
                       'stress': {'form': 'поли́вка', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/поливка'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'жіночий',
                                                         'cases': {   'називний': {   'singular': 'поли́вка',
                                                                                      'plural': 'поли́вки'},
                                                                      'родовий': {   'singular': 'поли́вки',
                                                                                     'plural': 'поли́вок'},
                                                                      'давальний': {   'singular': 'поли́вці',
                                                                                       'plural': 'поли́вкам'},
                                                                      'знахідний': {   'singular': 'поли́вку',
                                                                                       'plural': 'поли́вки'},
                                                                      'орудний': {   'singular': 'поли́вкою',
                                                                                     'plural': 'поли́вками'},
                                                                      'місцевий': {   'singular': 'поли́вці',
                                                                                      'plural': 'поли́вках'},
                                                                      'кличний': {   'singular': 'поли́вко',
                                                                                     'plural': 'поли́вки'}}}},
                       'distinction_note': 'Автентична українська назва першої рідкої страви (юшки, супу; «поливка з '
                                           "грибами, поливка з вушками»). Не плутати з глазур'ю «по́ли́вка».",
                       'meaning': {'definitions': ['Рідка страва; юшка, суп.'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'ПОЛИ́ВКА, и, ж., розм. Те саме, що '
                                                                        'полива́ння. Там [у палісаднику] якраз '
                                                                        'відбувалася вечірня поливка квітів (Смолич, '
                                                                        'І, 1958, 63); При коренях молодих дерев ще не '
                                                                        'висохла від поливки земля (Кучер, Чорноморці, '
                                                                        '1956, 433).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                 'quote': 'Поливка, -ки, ж. 1) Соус, подливка. Вже двірської поливки '
                                                          'хлиснув, а оброкового хліба покушав. Ном. № 1312. 2) Суп. '
                                                          'Вх. Уг. 261. 3) Каша с тертым конопляным семенем. Мнж. 190. '
                                                          'Ум. поливочка. Усядь, брате, на лавичку, сербай добру '
                                                          'поливочку. Гол. I. 209.',
                                                 'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                    'Борисом Грінченком в умовах дії антиукраїнських '
                                                                    'імперських указів (Валуєвського циркуляра 1863 р. '
                                                                    'та Емського указу 1876 р.).'}}],
    'помісний': [   {   'headword': 'по́місни́й',
                        'short_label': 'стосовний до собору помісної православної церкви (церк.)',
                        'gloss': 'local, autocephalous (church council, local church)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈpɔm⁽ʲ⁾isnɪj]'},
                        'stress': {   'form': 'по́місни́й',
                                      'source': 'ВТС',
                                      'url': 'https://slovnyk.me/dict/vts/помісний'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Церковний термін: прикметник до помісна церква, Помісний собор '
                                            '(національний церковний собор). Не плутати з феодальним поміщицьким '
                                            'володінням «помі́сний».',
                        'meaning': {   'definitions': [   'Стосовний до помісної церкви; соборний; також прикм. до '
                                                          'помісь.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ПО́МІСНИ́Й, по́місна́, по́місне́. Прикм. до '
                                                                         'по́місь 1. З одержанням у результаті '
                                                                         'схрещування помісних тварин робота '
                                                                         'селекціонера не закінчується, а тільки '
                                                                         'починається (Наука.., 8, 1956,32); Помісні '
                                                                         'курчата краще виживають (Птахівн., 1955, 9).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'помі́сний',
                        'short_label': "пов'язаний із дворянським маєтком, помістям або поміщиками (іст.)",
                        'gloss': 'manorial, landed estate, estate-based (hist., feudal)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[pɔˈm⁽ʲ⁾isnɪj]'},
                        'stress': {'form': 'помі́сний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/помісний'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': "Історичний соціально-економічний термін: пов'язаний із земельним помістям "
                                            'дворян (помісна система, помісне дворянство). Не плутати з церковним '
                                            '«по́місни́й».',
                        'meaning': {'definitions': ["Пов'язаний з помістям, землеволодінням."], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ПОМІ́СНИЙ, а, е. Прикм. до помі́стя. Поряд з '
                                                                         'боярськими та монастирськими вотчинами '
                                                                         'виникло помісне землеволодіння (Іст. СРСР, '
                                                                         'І, 1957, 96).',
                                                           'sovietization_risk': 1,
                                                           'keywords': ['срср'],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості; цитує радянські джерела з '
                                                                              'історії СРСР.'},
                        'pre_soviet_witness': None}],
    'поставляти': [   {   'headword': 'поста́вляти',
                          'short_label': 'поставити багато предметів, розставити по місцях (док., заст.)',
                          'gloss': 'place, put or arrange many items in their places (perf., arch.)',
                          'pos': 'verb',
                          'cefr': 'B1',
                          'heritage_status': {   'classification': 'authentic-archaism',
                                                 'is_russianism': False,
                                                 'russian_shadow': False,
                                                 'vesum_attested': True,
                                                 'warning_severity': 'treasured'},
                          'pronunciation': {'ipa': '[pɔˈstɑu̯lʲɐtɪ]'},
                          'stress': {   'form': 'поста́вляти',
                                        'source': 'ВТС',
                                        'url': 'https://slovnyk.me/dict/vts/поставляти'},
                          'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                          'distinction_note': 'Застаріле доконане дієслово: розставити велику кількість речей на '
                                              'поверхні (посуд на стіл, стільці в кімнаті; док. вид). Не плутати з '
                                              'калькованим «поставля́ти».',
                          'meaning': {   'definitions': ['Поставити все або багато чого-небудь (доконаний вид).'],
                                         'source': 'ВТС'},
                          'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                             'definition': 'ПОСТА́ВЛЯТИ, яю, яєш, док., перех., заст. '
                                                                           'Поставити ( див. поста́вити¹). Нема '
                                                                           'нікого. То вчора Уляна горстки біля '
                                                                           'повітки поста́вляла, от воно й здається, '
                                                                           'що хтось причаївся (Тют., Вир, 1964, 431); '
                                                                           'Було і к весіллю зовсім приберуться і '
                                                                           'будинки поставляють кам’яні, і коней '
                                                                           'вороних позапрягають, — аж лихо! (Вовчок, '
                                                                           'І, 1955, 107); [Корж:] У нас єсть закон '
                                                                           'дідівський — не ми його поставляли, не нам '
                                                                           'і ламать його (Вас., III, 1960, 56).',
                                                             'sovietization_risk': 0,
                                                             'keywords': [],
                                                             'historical_note': 'Зафіксовано в радянський період '
                                                                                '(СУМ-11). Наведено для '
                                                                                'лексикографічної прозорості.'},
                          'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                    'quote': 'Поставляти, -ляю, -єш, гл. = поставити (во множ .). Баби '
                                                             'поставляли все. Грин. І. 146. Ой викопай, мати, глибокую '
                                                             'яму, та поховай, мати, сю славную пару, та поставляй, '
                                                             'мати, хрести золотії. Мет. 96. Поруйнував хати та й не '
                                                             'поставляв. К. Іов. 44.',
                                                    'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                       'Борисом Грінченком в умовах дії '
                                                                       'антиукраїнських імперських указів '
                                                                       '(Валуєвського циркуляра 1863 р. та Емського '
                                                                       'указу 1876 р.).'}},
                      {   'headword': 'поставля́ти',
                          'short_label': 'доставляти продукцію, постачати товари за договором (калька, :bad)',
                          'gloss': 'supply, deliver goods/commodities under contract (imperf.; calque)',
                          'pos': 'verb',
                          'cefr': 'B1',
                          'heritage_status': {   'classification': 'calque',
                                                 'is_russianism': True,
                                                 'russian_shadow': True,
                                                 'vesum_attested': True,
                                                 'warning_severity': 'caution',
                                                 'calque_warning': {'standard_alternatives': ['постачати']}},
                          'pronunciation': {'ipa': '[pɔstɐu̯ˈlʲɑtɪ]'},
                          'stress': {   'form': 'поставля́ти',
                                        'source': 'ВТС',
                                        'url': 'https://slovnyk.me/dict/vts/поставляти'},
                          'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                          'distinction_note': 'Економічно-канцелярська калька з рос. «поставлять», маркована у ВЕСУМ '
                                              'як :bad. У сучасній літературній нормі рекомендовано вживати питоме '
                                              '«постачати». Не плутати з питомим доконаним «поста́вляти».',
                          'meaning': {   'definitions': [   'Здійснювати поставку, постачати що-небудь за договором '
                                                            '(недоконаний вид; нерекомендоване).'],
                                         'source': 'ВТС'},
                          'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                             'definition': 'ПОСТАВЛЯ́ТИ, я́ю, я́єш, недок., '
                                                                           'ПОСТА́ВИТИ, влю, виш; мн. поставлять; '
                                                                           'док., перех. Доставляти, постачати '
                                                                           'що-небудь комусь. Душі не чув Олексій, так '
                                                                           'любив свою дочечку, і об усім для неї '
                                                                           'вбивався. Хоч вона нічого і не бажала для '
                                                                           'себе, так батько усе їй поставляв '
                                                                           '(Кв.-Осн., II, 1956, 313); Шефи його '
                                                                           '[Врангеля] під тиском робітничих мас '
                                                                           'змушені були тимчасово відмовитись '
                                                                           'поставляти зброю в Крим (Гончар, II, 1959, '
                                                                           '380); Нині Радянська Вірменія поставляє '
                                                                           'машини, устаткування і прилади.. у 70 '
                                                                           'країн світу (Ком. Укр., 3, 1967, 24); '
                                                                           'Україна, починаючи з XVII ст., поставляла '
                                                                           'в Росію першокласні співочі кадри (Укр. '
                                                                           'клас. опера, 1957, 40); [Юрій:] Торік по '
                                                                           'контракту батько мав поставити Семиренкові '
                                                                           'сто двадцять тисяч пудів буряку. Через '
                                                                           'селянські страйки не поставив і заплатив '
                                                                           'неустойку (Сміл., Черв. троянда, 1955, '
                                                                           '51); Головинські розробки.. повинні були '
                                                                           'поставити для будівництва Мавзолею В. І. '
                                                                           'Леніна великі моноліти (Наука.., 4, 1962, '
                                                                           '5).',
                                                             'sovietization_risk': 1,
                                                             'keywords': ['ленін', 'радянськ'],
                                                             'historical_note': 'Зафіксовано в радянський період '
                                                                                '(СУМ-11). Наведено для '
                                                                                'лексикографічної прозорості; містить '
                                                                                'радянські ідеологізовані цитати '
                                                                                '(Ленін).'},
                          'pre_soviet_witness': None}],
    'складуватися': [   {   'headword': 'скла́дуватися',
                            'short_label': 'зосереджуватися на складі, зберігатися складським способом (недок.)',
                            'gloss': 'be stored in a warehouse, accumulate in storage (imperf.)',
                            'pos': 'verb',
                            'cefr': 'B2',
                            'heritage_status': {   'classification': 'standard',
                                                   'is_russianism': False,
                                                   'russian_shadow': False,
                                                   'vesum_attested': True},
                            'pronunciation': {'ipa': '[ˈsklɑduwɐtɪsʲɐ]'},
                            'stress': {   'form': 'скла́дуватися',
                                          'source': 'ВТС',
                                          'url': 'https://slovnyk.me/dict/vts/складуватися'},
                            'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                            'distinction_note': 'Означає накопичуватися або розміщуватися на складі (вантажі '
                                                'складуються на рампі). Не плутати з формуванням життєвих обставин '
                                                '«складува́тися».',
                            'meaning': {   'definitions': ['Зосереджуватися на складі; зберігатися в складі.'],
                                           'source': 'ВТС'},
                            'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                               'definition': 'СКЛА́ДУВАТИСЯ, уюся, уєшся, недок., '
                                                                             'рідко. Те саме, що склада́тися. Для '
                                                                             'таких бідних і одсталих країв, як ті, з '
                                                                             'котрих складувалась Росія,.. '
                                                                             'централізація була.. [неминучою] формою '
                                                                             'громадської організації (Драг., І, 1970, '
                                                                             '111); Царевич випустив у царину печеного '
                                                                             'бугая; де він пройде, там пшениця сама в '
                                                                             'копи складується й молотиться (Стор., І, '
                                                                             '1957, 66).',
                                                               'sovietization_risk': 0,
                                                               'keywords': [],
                                                               'historical_note': 'Зафіксовано в радянський період '
                                                                                  '(СУМ-11). Наведено для '
                                                                                  'лексикографічної прозорості.'},
                            'pre_soviet_witness': None},
                        {   'headword': 'складува́тися',
                            'short_label': 'формуватися з елементів, виникати як результат обставин (недок.)',
                            'gloss': 'take shape, form, develop out of elements or conditions (imperf.)',
                            'pos': 'verb',
                            'cefr': 'B2',
                            'heritage_status': {   'classification': 'standard',
                                                   'is_russianism': False,
                                                   'russian_shadow': False,
                                                   'vesum_attested': True},
                            'pronunciation': {'ipa': '[sklɐduˈwɑtʲisʲɐ]'},
                            'stress': {   'form': 'складува́тися',
                                          'source': 'ВТС',
                                          'url': 'https://slovnyk.me/dict/vts/складуватися'},
                            'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                            'distinction_note': 'Означає формуватися з частин, набирати вигляду (погляди складуються, '
                                                'обставини складуються). Не плутати з розміщенням на складі '
                                                '«скла́дуватися».',
                            'meaning': {   'definitions': ['Формуватися, утворюватися з окремих частин; розвиватися.'],
                                           'source': 'ВТС'},
                            'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                               'definition': 'СКЛАДУВА́ТИСЯ, у́ється, недок., спец. '
                                                                             'Пас. до складува́ти.',
                                                               'sovietization_risk': 0,
                                                               'keywords': [],
                                                               'historical_note': 'Зафіксовано в радянський період '
                                                                                  '(СУМ-11). Наведено для '
                                                                                  'лексикографічної прозорості.'},
                            'pre_soviet_witness': None}],
    'склепувати': [   {   'headword': 'скле́пувати',
                          'short_label': "з'єднувати деталі клепками, заклепками або обручами (недок.)",
                          'gloss': 'rivet together, fasten with rivets or hoops (imperf.)',
                          'pos': 'verb',
                          'cefr': 'B2',
                          'heritage_status': {   'classification': 'standard',
                                                 'is_russianism': False,
                                                 'russian_shadow': False,
                                                 'vesum_attested': True},
                          'pronunciation': {'ipa': '[ˈsklɛpuwɐtɪ]'},
                          'stress': {   'form': 'скле́пувати',
                                        'source': 'ВТС',
                                        'url': 'https://slovnyk.me/dict/vts/склепувати'},
                          'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                          'distinction_note': "Технічне значення: з'єднувати металеві листи чи клепки бочки "
                                              'заклепками. Не плутати з «склепува́ти» (діал. мурувати склеп або '
                                              'склепіння).',
                          'meaning': {   'definitions': [   "Клепаючи, з'єднувати, скріплювати що-небудь заклепками "
                                                            'або клепками.'],
                                         'source': 'СУМ-20'},
                          'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                             'definition': 'СКЛЕ́ПУВАТИ, ую, уєш, недок., СКЛЕПА́ТИ, '
                                                                           'склепа́ю, склепа́єш і склеплю́, скле́плеш; '
                                                                           'мн. склепа́ють і скле́плють; док., перех. '
                                                                           '1. Клепаючи, з’єднувати, скріплювати '
                                                                           'що-небудь. Склепали гострими кінцями '
                                                                           'докупи дві звичайні коси, приладнали '
                                                                           'кілька грузил, а до п’ят коси прив’язали '
                                                                           'по вірьовці (Донч., І, 1956, 51); '
                                                                           '*Образно. — Бачив, як гнів його брови '
                                                                           'склепав? (Стельмах, І, 1962, 26). 2. '
                                                                           'тільки док., розм. Клепаючи, виготовити '
                                                                           'що-небудь. Майстер узяв великий аркуш '
                                                                           'білого цинкового заліза, покраяв його і на '
                                                                           'очах у хлопців хутко склепав виварку на '
                                                                           'білизну (Мик., II, 1957, 474). 3. перен. '
                                                                           'Робити що-небудь наспіх, недбало, абияк. — '
                                                                           'От, — кажу, — хвалько небесний! Три '
                                                                           'шпаківні склепав, а балачок на всю школу! '
                                                                           '(Донч., VI, 1957, 250); — Так і тримали '
                                                                           'без суду, поки я сам не допоміг прокурору '
                                                                           'склепати на себе вирок і кайдани за втечу, '
                                                                           '— розповів згодом Дебрич Юркові (Козл., Ю. '
                                                                           'Крук, 1957, 427).',
                                                             'sovietization_risk': 0,
                                                             'keywords': [],
                                                             'historical_note': 'Зафіксовано в радянський період '
                                                                                '(СУМ-11). Наведено для '
                                                                                'лексикографічної прозорості.'},
                          'pre_soviet_witness': None},
                      {   'headword': 'склепува́ти',
                          'short_label': 'будувати склеп, мурувати склепіння (діал., недок.)',
                          'gloss': 'build a vault, build a crypt or vaulted ceiling (dialectal, imperf.)',
                          'pos': 'verb',
                          'cefr': 'B2',
                          'heritage_status': {   'classification': 'authentic-dialectism',
                                                 'is_russianism': False,
                                                 'russian_shadow': False,
                                                 'vesum_attested': True,
                                                 'warning_severity': 'treasured'},
                          'pronunciation': {'ipa': '[sklɛpuˈwɑtɪ]'},
                          'stress': {   'form': 'склепува́ти',
                                        'source': 'ВТС',
                                        'url': 'https://slovnyk.me/dict/vts/склепувати'},
                          'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                          'distinction_note': "Діалектне значення: мурувати підземний склеп або кам'яне склепіння "
                                              '(«казав пан Каньовський ще й склеп склепувати»). Не плутати зі '
                                              'слюсарним клепанням заклепками «скле́пувати».',
                          'meaning': {   'definitions': [   'Діалектне або застаріле: будувати склеп, мурувати '
                                                            'склепіння.'],
                                         'source': 'СУМ-20'},
                          'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                             'definition': 'СКЛЕПУВА́ТИ, у́ю, у́єш, недок., перех., '
                                                                           'діал. Будувати склеп (у 1 знач.). Ой же '
                                                                           'казав пан Каньовський ще й склеп '
                                                                           'склепувати, молоду Бондарівну гарно '
                                                                           'поховати (Чуб., V, 1874, 428).',
                                                             'sovietization_risk': 0,
                                                             'keywords': [],
                                                             'historical_note': 'Зафіксовано в радянський період '
                                                                                '(СУМ-11). Наведено для '
                                                                                'лексикографічної прозорості.'},
                          'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                    'quote': 'Склепувати, -пую, -єш, гл. = склепити. Ой же казав пан '
                                                             'Каньовський ще й склеп склепувати. Чуб. V. 428.',
                                                    'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                       'Борисом Грінченком в умовах дії '
                                                                       'антиукраїнських імперських указів '
                                                                       '(Валуєвського циркуляра 1863 р. та Емського '
                                                                       'указу 1876 р.).'}}],
    'совковий': [   {   'headword': 'со́вковий',
                        'short_label': 'стосовний до со́вки (нічного метелика родини Noctuidae)',
                        'gloss': 'pertaining to the owlet moth (Noctuidae moth family)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈsɔu̯kɔwɪj]'},
                        'stress': {'form': 'со́вковий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/совковий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Ентомологічний термін: стосовний до совки (нічного метелика родини '
                                            'совок). Не плутати з совком як ручним інструментом або радянщиною '
                                            '«совко́вий».',
                        'meaning': {   'definitions': [   'Прикметник до совка (нічний метелик родини совок); '
                                                          'стосовний до цієї родини комах.'],
                                       'source': 'СУМ-20'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СО́ВКОВИЙ, а, е. 1. Прикм. до со́вка. 2. у '
                                                                         'знач. ім. со́вкові, вих, мн. Назва родини '
                                                                         'нічних метеликів, голова яких нагадує голову '
                                                                         'сови.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'совко́вий',
                        'short_label': 'стосовний до совка (лопатки) або перен. радянський (зневажл.)',
                        'gloss': 'pertaining to a dustpan / scoop, or colloq. Soviet-style',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[sɔu̯ˈkɔwɪj]'},
                        'stress': {'form': 'совко́вий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/совковий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': "Пов'язаний із совком як господарським знаряддям (совкова лопата) або "
                                            'розмовне зневажливе позначення радянських порядків чи менталітету. Не '
                                            'плутати з нічним метеликом «со́вковий».',
                        'meaning': {   'definitions': [   'Прикметник до совок (лопатка або совок); перен. розм. '
                                                          'іронічне позначення радянського способу життя або '
                                                          'мислення.'],
                                       'source': 'СУМ-20'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СОВКО́ВИЙ, а, е. Прикм. до сово́к; // Який '
                                                                         'формою нагадує совок, зробл. у вигляді '
                                                                         'совка. Для виготовлення котлованів '
                                                                         'користуються кінними плугами, кінними '
                                                                         'совковими, лопатами, а ще краще бульдозерами '
                                                                         '(Овоч. закр. і відкр. грунту, 1957, 100).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'сопуха': [   {   'headword': 'со́пу́ха',
                      'short_label': 'отвір у печі або димарі для очищення сажі (пічний отвір)',
                      'gloss': 'soot door, chimney cleaning hole, flue cleanout',
                      'pos': 'noun',
                      'cefr': 'B2',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[ˈsɔpuxɐ]'},
                      'stress': {'form': 'со́пу́ха', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сопуха'},
                      'morphology': {   'pos': 'іменник',
                                        'paradigm': {   'kind': 'noun',
                                                        'gender': 'жіночий',
                                                        'cases': {   'називний': {   'singular': 'со́пуха',
                                                                                     'plural': 'со́пухи'},
                                                                     'родовий': {   'singular': 'со́пухи',
                                                                                    'plural': 'со́пух'},
                                                                     'давальний': {   'singular': 'со́пусі',
                                                                                      'plural': 'со́пухам'},
                                                                     'знахідний': {   'singular': 'со́пуху',
                                                                                      'plural': 'со́пухи'},
                                                                     'орудний': {   'singular': 'со́пухою',
                                                                                    'plural': 'со́пухами'},
                                                                     'місцевий': {   'singular': 'со́пусі',
                                                                                     'plural': 'со́пухах'},
                                                                     'кличний': {   'singular': 'со́пухо',
                                                                                    'plural': 'со́пухи'}}}},
                      'distinction_note': 'Побутове значення: отвір у комині чи печі для вигрібання сажі. Не плутати з '
                                          'їдким чадним димом або лайливим словом «сопу́ха».',
                      'meaning': {'definitions': ['Отвір у димарі або печі для вигрібання сажі.'], 'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'СО́ПУ́ХА, и, ж., діал. 1. Сажа. — Якби не він, '
                                                                       'та й би мене аж на весні найшли, якби сопуха з '
                                                                       'печі аж на дорогу вдарила (Стеф., Вибр., 1945, '
                                                                       '99); *У порівн. Сорочки чорні, як сопуха (П. '
                                                                       'Куліш, Вибр., 1969, 127). 2. Сморід.',
                                                         'sovietization_risk': 0,
                                                         'keywords': [],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної '
                                                                            'прозорості.'},
                      'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                'quote': 'Сопуха, -хи, ж. 1) Сажа. Грин. II. 178. 2) Испачканная в '
                                                         'сажу рубаха, черная, как сажа. Росхристана сорочка-сопуха. '
                                                         'Г. Барв. 23.',
                                                'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                   'Борисом Грінченком в умовах дії антиукраїнських '
                                                                   'імперських указів (Валуєвського циркуляра 1863 р. '
                                                                   'та Емського указу 1876 р.).'}},
                  {   'headword': 'сопу́ха',
                      'short_label': 'густий їдкий дим, кіптява, або неохайна замурзана людина (розм.)',
                      'gloss': 'acrid smoke, soot cloud, or dirty disheveled person (colloq.)',
                      'pos': 'noun',
                      'cefr': 'B2',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[sɔˈpuxɐ]'},
                      'stress': {'form': 'сопу́ха', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сопуха'},
                      'morphology': {   'pos': 'іменник',
                                        'paradigm': {   'kind': 'noun',
                                                        'gender': 'жіночий',
                                                        'cases': {   'називний': {   'singular': 'сопу́ха',
                                                                                     'plural': 'сопу́хи'},
                                                                     'родовий': {   'singular': 'сопу́хи',
                                                                                    'plural': 'сопу́х'},
                                                                     'давальний': {   'singular': 'сопу́сі',
                                                                                      'plural': 'сопу́хам'},
                                                                     'знахідний': {   'singular': 'сопу́ху',
                                                                                      'plural': 'сопу́хи / сопу́х'},
                                                                     'орудний': {   'singular': 'сопу́хою',
                                                                                    'plural': 'сопу́хами'},
                                                                     'місцевий': {   'singular': 'сопу́сі',
                                                                                     'plural': 'сопу́хах'},
                                                                     'кличний': {   'singular': 'сопу́хо',
                                                                                    'plural': 'сопу́хи'}}}},
                      'distinction_note': 'Означає їдкий дим або забруднену сажею неохайну особу (перен., лайл.). Не '
                                          'плутати з отвором у димарі «со́пу́ха».',
                      'meaning': {   'definitions': ['Густий їдкий дим, сморід або засмальцьована людина.'],
                                     'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'СОПУ́ХА, и, ж., розм. Жін. до сопу́н.',
                                                         'sovietization_risk': 0,
                                                         'keywords': [],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної '
                                                                            'прозорості.'},
                      'pre_soviet_witness': None}],
    'сосковий': [   {   'headword': 'со́сковий',
                        'short_label': 'стосовний до соска грудної залози (анат.)',
                        'gloss': 'nipple-related, mammillary, papillary (anat.)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈsɔskɔwɪj]'},
                        'stress': {'form': 'со́сковий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сосковий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Анатомічний термін: стосовний до грудного соска (соскова лінія, сосковий '
                                            'відросток). Не плутати з технічною деталлю доїльного апарата «соско́вий».',
                        'meaning': {'definitions': ['Стосовний до соска тіла.'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СО́СКОВИЙ, а, е. Прикм. до со́ска. Через 40 '
                                                                         '—50 хвилин після народження телят випоювали '
                                                                         'з соскової напувалки молозивом (Соц. твар., '
                                                                         '1, 1956, 51).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'соско́вий',
                        'short_label': 'стосовний до соска як насадки доїльного апарата (техн.)',
                        'gloss': 'teat-cup related (agricultural machinery)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[sɔˈskɔwɪj]'},
                        'stress': {'form': 'соско́вий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сосковий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Сільськогосподарський технічний термін: стосовний до насадок апарата '
                                            'машинного доїння (соскова гума). Не плутати з анатомічним терміном '
                                            '«со́сковий».',
                        'meaning': {   'definitions': ['Прикметник до сосок (технічна деталь у тваринництві).'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СОСКО́ВИЙ, а, е. Прикм. до сосо́к.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'співанка': [   {   'headword': 'спі́ванка',
                        'short_label': 'репетиція хору, спільна репетиція хорового колективу',
                        'gloss': 'choir rehearsal, choral practice session',
                        'pos': 'noun',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈsp⁽ʲ⁾iwɐnkɐ]'},
                        'stress': {'form': 'спі́ванка', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/співанка'},
                        'morphology': {   'pos': 'іменник',
                                          'paradigm': {   'kind': 'noun',
                                                          'gender': 'жіночий',
                                                          'cases': {   'називний': {   'singular': 'спі́ванка',
                                                                                       'plural': 'спі́ванки'},
                                                                       'родовий': {   'singular': 'спі́ванки',
                                                                                      'plural': 'спі́ванок'},
                                                                       'давальний': {   'singular': 'спі́ванці',
                                                                                        'plural': 'спі́ванкам'},
                                                                       'знахідний': {   'singular': 'спі́ванку',
                                                                                        'plural': 'спі́ванки'},
                                                                       'орудний': {   'singular': 'спі́ванкою',
                                                                                      'plural': 'спі́ванками'},
                                                                       'місцевий': {   'singular': 'спі́ванці',
                                                                                       'plural': 'спі́ванках'},
                                                                       'кличний': {   'singular': 'спі́ванко',
                                                                                      'plural': 'спі́ванки'}}}},
                        'distinction_note': 'Означає репетицію хору або заняття співацького колективу (вечорами ходив '
                                            'на співанки до школи). Не плутати з народною піснею чи коломийкою '
                                            '«спі́ва́нка».',
                        'meaning': {'definitions': ['Репетиція хору.'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СПІ́ВАНКА, и, ж. Репетиція хору. Серафима '
                                                                         'Миколаївна, помітивши мій голос і слух, '
                                                                         'відібрала мене до свого хору, і я з своєю '
                                                                         'молодшою сестрою Оксаною вечорами ходив на '
                                                                         'співанки до школи (Тич., III, 1957, 133); '
                                                                         'Невихід на співанку трьох голосів вона, '
                                                                         'безсумнівно, сприйняла б як тяжку особисту '
                                                                         'образу (Смолич, Мир.., 1958, 31).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'спі́ва́нка',
                        'short_label': 'народна пісня, коломийка, пісенний твір (фольк.)',
                        'gloss': 'song, folk song, kolomyika, traditional tune (folk.)',
                        'pos': 'noun',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[sp⁽ʲ⁾iˈwɑnkɐ]'},
                        'stress': {   'form': 'спі́ва́нка',
                                      'source': 'ВТС',
                                      'url': 'https://slovnyk.me/dict/vts/співанка'},
                        'morphology': {   'pos': 'іменник',
                                          'paradigm': {   'kind': 'noun',
                                                          'gender': 'жіночий',
                                                          'cases': {   'називний': {   'singular': 'співа́нка',
                                                                                       'plural': 'співа́нки'},
                                                                       'родовий': {   'singular': 'співа́нки',
                                                                                      'plural': 'співа́нок'},
                                                                       'давальний': {   'singular': 'співа́нці',
                                                                                        'plural': 'співа́нкам'},
                                                                       'знахідний': {   'singular': 'співа́нку',
                                                                                        'plural': 'співа́нки'},
                                                                       'орудний': {   'singular': 'співа́нкою',
                                                                                      'plural': 'співа́нками'},
                                                                       'місцевий': {   'singular': 'співа́нці',
                                                                                       'plural': 'співа́нках'},
                                                                       'кличний': {   'singular': 'співа́нко',
                                                                                      'plural': 'співа́нки'}}}},
                        'distinction_note': 'Традиційний фольклорний жанр: народна пісня, приспівка, коломийка '
                                            '(колискова співанка). Не плутати з хоровою репетицією «спі́ванка».',
                        'meaning': {   'definitions': ['Те саме, що пісня; коротка пісня, коломийка; пісенні звуки.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СПІ́ВА́НКА, и, ж. Те саме, що пі́сня. Вона '
                                                                         'тоненьким голосом затягнула колискову '
                                                                         'співанку (Фр., V, 1951, 119); Жителі Коломиї '
                                                                         'славляться вмінням складати жанрові '
                                                                         'лірично-побутові співанки (Визначні місця '
                                                                         'Укр., 1958, 540); Ліричні співанки і думи '
                                                                         'Федьковича створені під значним впливом '
                                                                         'гуцульської народнопісенної творчості. Поет '
                                                                         'творчо використовує стиль, поетику народних '
                                                                         'ліричних пісень (Іст. укр. літ., І, 1954, '
                                                                         '334); Поетеса Ганна подала думку: гуртом '
                                                                         'скласти про свою вчительку співанку, добрати '
                                                                         'мелодію (Вол., Місячне срібло, 1961, 225); '
                                                                         '// Пісенні звуки. З поля приносив вітер '
                                                                         'співанку (Март., Тв., 1954, 100).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                  'quote': 'Співанка, -ки, ж. Песнь. Не співанку я співала. Гол. І. '
                                                           '172. Ум. співаночка. Лукаш. 146.',
                                                  'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                     'Борисом Грінченком в умовах дії антиукраїнських '
                                                                     'імперських указів (Валуєвського циркуляра 1863 '
                                                                     'р. та Емського указу 1876 р.).'}}],
    'споритися': [   {   'headword': 'спо́ритися',
                         'short_label': 'вести словесну суперечку, сперечатися (розм., недок.)',
                         'gloss': 'argue, dispute, bicker with words (colloq., imperf.)',
                         'pos': 'verb',
                         'cefr': 'B1',
                         'heritage_status': {   'classification': 'standard',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True},
                         'pronunciation': {'ipa': '[ˈspɔrɪtɪsʲɐ]'},
                         'stress': {   'form': 'спо́ритися',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/споритися'},
                         'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                         'distinction_note': 'Означає змагатися в словах, сперечатися («споритися за межу»). Не '
                                             'плутати з успішним просуванням роботи «спори́тися».',
                         'meaning': {'definitions': ['Те саме, що сперечатися; вести суперечку.'], 'source': 'ВТС'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СПО́РИТИСЯ, рюся, ришся, недок., розм. Те '
                                                                          'саме, що спо́рити 1. Мужик із жінкою часто '
                                                                          'спорились: кому з них робити трудніш '
                                                                          '(Україна.., І, 1960, 214); Науково з ним '
                                                                          'споритися вона не годна (Коб., III, 1956, '
                                                                          '323); Часом княгиня Ольга жахається, — що ж '
                                                                          'це сталось нині на Русі? Адже споряться між '
                                                                          'собою землі, городи, села, всі люди! Куди, '
                                                                          'куди йде Русь? (Скл., Святослав, 1959, 53).',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                   'quote': 'Споритися 2, -рюся, -ришся, гл. 1) Спорить. Спориться як '
                                                            'за батьківщину. Ном. № 2669. 2) Воли споряться. Не парные '
                                                            'волы несогласно идут в паре. Мнж. 167.',
                                                   'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                      'Борисом Грінченком в умовах дії антиукраїнських '
                                                                      'імперських указів (Валуєвського циркуляра 1863 '
                                                                      'р. та Емського указу 1876 р.).'}},
                     {   'headword': 'спори́тися',
                         'short_label': 'іти успішно, ладитися, приносити швидкий результат (недок.)',
                         'gloss': 'go smoothly, make fast headway, prosper, thrive (imperf.)',
                         'pos': 'verb',
                         'cefr': 'B1',
                         'heritage_status': {   'classification': 'standard',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True},
                         'pronunciation': {'ipa': '[spɔˈrɪtɪsʲɐ]'},
                         'stress': {   'form': 'спори́тися',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/споритися'},
                         'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                         'distinction_note': 'Означає ладитися, йти швидко та успішно («робота спориться в руках»). Не '
                                             'плутати зі словесною сваркою «спо́ритися».',
                         'meaning': {'definitions': ['Удаватися, успішно йти; ладитися.'], 'source': 'ВТС'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СПОРИ́ТИСЯ, ри́ться, недок., розм. Іти, '
                                                                          'здійснюватися успішно і швидко (про роботу, '
                                                                          'діяльність). Труд спориться, коли співа '
                                                                          'душа. Хай буде це чи повість, чи поема '
                                                                          '(Дмит., В обіймах сонця, 1958, 11); Андрій '
                                                                          'хотів того дня закінчити роботу над діжкою, '
                                                                          'але ніяк не спорилася в нього праця (Томч., '
                                                                          'Готель.., 1960, 90); Життя справді стає '
                                                                          'дедалі кращим і веселішим. А коли добре '
                                                                          'живеться, то й робота спориться (Ком. Укр., '
                                                                          '7,1960, 4).',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                   'quote': 'Споритися, -рюся, -ришся, гл. 1) Умножаться, '
                                                            'прибавляться, увеличиваться. 2) Спориться, удаваться.',
                                                   'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                      'Борисом Грінченком в умовах дії антиукраїнських '
                                                                      'імперських указів (Валуєвського циркуляра 1863 '
                                                                      'р. та Емського указу 1876 р.).'}}],
    'справниця': [   {   'headword': 'спра́вниця',
                         'short_label': 'дружина або дочка повітового справника (іст., дорев.)',
                         'gloss': "district police chief's wife or daughter (hist.)",
                         'pos': 'noun',
                         'cefr': 'B2',
                         'heritage_status': {   'classification': 'authentic-historism',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True,
                                                'warning_severity': 'treasured'},
                         'pronunciation': {'ipa': '[ˈsprɑu̯nɪt͡sʲɐ]'},
                         'stress': {   'form': 'спра́вниця',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/справниця'},
                         'morphology': {   'pos': 'іменник',
                                           'paradigm': {   'kind': 'noun',
                                                           'gender': 'жіночий',
                                                           'cases': {   'називний': {   'singular': 'спра́вниця',
                                                                                        'plural': 'спра́вниці'},
                                                                        'родовий': {   'singular': 'спра́вниці',
                                                                                       'plural': 'спра́вниць'},
                                                                        'давальний': {   'singular': 'спра́вниці',
                                                                                         'plural': 'спра́вницям'},
                                                                        'знахідний': {   'singular': 'спра́вницю',
                                                                                         'plural': 'спра́вниць'},
                                                                        'орудний': {   'singular': 'спра́вницею',
                                                                                       'plural': 'спра́вницями'},
                                                                        'місцевий': {   'singular': 'спра́вниці',
                                                                                        'plural': 'спра́вницях'},
                                                                        'кличний': {   'singular': 'спра́внице',
                                                                                       'plural': 'спра́вниці'}}}},
                         'distinction_note': 'Історичний соціальний статус: жінка або дочка повітового справника '
                                             '(дореволюційної поліції). Не плутати з судово-адміністративною установою '
                                             '«справни́ця».',
                         'meaning': {'definitions': ['Дружина або дочка справника.'], 'source': 'ВТС'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СПРА́ВНИЦЯ, і, ж., дорев. Дружина '
                                                                          'справника.',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': None},
                     {   'headword': 'справни́ця',
                         'short_label': 'присутствене місце, судова або адміністративна установа (іст., дорев.)',
                         'gloss': 'courtroom, administrative office, governmental bureau (hist.)',
                         'pos': 'noun',
                         'cefr': 'B2',
                         'heritage_status': {   'classification': 'authentic-historism',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True,
                                                'warning_severity': 'treasured'},
                         'pronunciation': {'ipa': '[sprɐu̯ˈnɪt͡sʲɐ]'},
                         'stress': {   'form': 'справни́ця',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/справниця'},
                         'morphology': {   'pos': 'іменник',
                                           'paradigm': {   'kind': 'noun',
                                                           'gender': 'жіночий',
                                                           'cases': {   'називний': {   'singular': 'справни́ця',
                                                                                        'plural': 'справни́ці'},
                                                                        'родовий': {   'singular': 'справни́ці',
                                                                                       'plural': 'справни́ць'},
                                                                        'давальний': {   'singular': 'справни́ці',
                                                                                         'plural': 'справни́цям'},
                                                                        'знахідний': {   'singular': 'справни́цю',
                                                                                         'plural': 'справни́ці'},
                                                                        'орудний': {   'singular': 'справни́цею',
                                                                                       'plural': 'справни́цями'},
                                                                        'місцевий': {   'singular': 'справни́ці',
                                                                                        'plural': 'справни́цях'},
                                                                        'кличний': {   'singular': 'справни́це',
                                                                                       'plural': 'справни́ці'}}}},
                         'distinction_note': 'Історичний термін на позначення судової чи адміністративної установи '
                                             '(присутствене місце: «В справниці осталися судці з авдитором»). Не '
                                             'плутати зі статусом дружини справника «спра́вниця».',
                         'meaning': {   'definitions': ['Історичне: присутствене місце (канцелярія, судова установа).'],
                                        'source': 'Грінченко'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СПРАВНИ́ЦЯ, і, ж., дорев. Присутствене '
                                                                          'місце. В справниці осталися судці з '
                                                                          'авдитором (Сл. Гр.).',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                   'quote': 'Справниця, -ці, ж. Присутственное место. В справниці '
                                                            'осталися судці з авдитором. Федьк. III. 150.',
                                                   'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                      'Борисом Грінченком в умовах дії антиукраїнських '
                                                                      'імперських указів (Валуєвського циркуляра 1863 '
                                                                      'р. та Емського указу 1876 р.).'}}],
    'становий': [   {   'headword': 'ста́новий',
                        'short_label': "пов'язаний із граматичним станом дієслова (лінгв., грамат.)",
                        'gloss': 'voice-related, grammatical voice (linguistics)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈstɑnɔwɪj]'},
                        'stress': {'form': 'ста́новий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/становий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Спеціальний мовознавчий термін: стосовний до категорії стану дієслова '
                                            '(становий суфікс, станові відношення). Не плутати з осьовим або '
                                            'соціальним «ста́нови́й».',
                        'meaning': {'definitions': ['Стосовний до граматичного стану дієслова.'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СТА́НОВИЙ, а, е, лінгв. Стос. до стану ( '
                                                                         'див. стан³ 5). Станові відношення в '
                                                                         'дієслові.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'ста́нови́й',
                        'short_label': 'осьовий, опорний (хребет); головна жила; іст. поліцейський пристав',
                        'gloss': 'vertebral, main spinal (ridge, aorta); hist. police officer',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[stɐnɔˈwɪj]'},
                        'stress': {   'form': 'ста́нови́й',
                                      'source': 'ВТС',
                                      'url': 'https://slovnyk.me/dict/vts/становий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Анатомічне та опорне значення (становий хребет, станова жила; іст. '
                                            'становий пристав). Не плутати з суспільними верствами «ста́новий».',
                        'meaning': {   'definitions': ['Хребетний, опорний; головний (про жилу або хребет).'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СТА́НОВИ́Й, ста́нова́, ста́нове́. 1. Стос. '
                                                                         'до стану ( див. стан³ 6); // Зумовлений '
                                                                         'приналежністю до якого-небудь стану. '
                                                                         'Українська шляхта і козацька старшина '
                                                                         'сподівались забезпечити собі станові '
                                                                         'економічні і політичні привілеї, зберегти у '
                                                                         'своїх руках адміністративні і судові органи '
                                                                         'влади (Іст. УРСР, І, 1953, 256); Революція '
                                                                         'не лишила каменя на камені від станових і '
                                                                         'класових привілеїв експлуататорів (Програма '
                                                                         'КПРС, 1961, 10). 2. Заснований на поділі '
                                                                         'суспільства на стани; власт. суспільству, '
                                                                         'поділеному на стани. Герої творів '
                                                                         'Квітки-Основ’яненка — це здебільшого селяни, '
                                                                         'сільські дівчата й парубки, що зазнають горя '
                                                                         'від панів-кріпосників, майнової і станової '
                                                                         'нерівності (Рад. літ-во, 3, 1971, 27); // '
                                                                         'Власт. привілейованим станам, який '
                                                                         'грунтується на зневажливому ставленні до '
                                                                         'інших станів. Мало кого поважала [Зоня] з '
                                                                         'сільських священиків. Вважала їх за тюхтіїв, '
                                                                         'позбавлених добрих манер, але почуття '
                                                                         'станової солідарності не покидало її ніколи '
                                                                         '(Вільде, III, 1968, 93). СТАНОВИ́Й¹, а́, е́, '
                                                                         'заст. 1. Стос. до стану ( див. стан² 3); '
                                                                         'пов’язаний з управлінням станом. Станове '
                                                                         'управління. Станови́й при́став див. '
                                                                         'при́став. 2. у знач. ім. станови́й, во́го, '
                                                                         'ч. Те саме, що Станови́й при́став ( див. '
                                                                         'при́став). З’їхались на заїзний двір два '
                                                                         'станові, і обидва були в одставці. Слово за '
                                                                         'слово і добалакались до того, як вони були '
                                                                         'становими в одному стані (Україна.., І, '
                                                                         '1960, 15); Через день у Медвин примчали '
                                                                         'справник, земський начальник, становий і '
                                                                         'кінні стражники (Стельмах, І, 1962, 632); *У '
                                                                         'порівн. Михалчевському хотілось поговорити з '
                                                                         'Василиною, розпитати в неї за все, заглянути '
                                                                         'в її душу, та Марія стриміла перед ним, як '
                                                                         'той становий (Н.-Лев., II, 1956, 142). '
                                                                         'СТАНОВИ́Й², а́, е́. Головний, основний. '
                                                                         'Станова́ жи́ла, заст. — те саме, що Спинни́й '
                                                                         'мо́зок ( див. спинни́й). — Так, кажеш, на '
                                                                         'поправку пішов? Головне, щоб станова жила '
                                                                         'сили набиралася, а вже від неї усе тіло '
                                                                         'почне здоров’ям наливатися (Кочура, Зол. '
                                                                         'грамота, 1960, 427). ∆ Станови́й я́кір, мор. '
                                                                         '— головний великий якір, який опускають з '
                                                                         'судна під час тривалої стоянки. В один з '
                                                                         'найміцніших поривів луснув канат від важкого '
                                                                         'станового якоря.., і шхуна ще безпорадніше '
                                                                         'заборсалася на одному меншому якорі (Тулуб, '
                                                                         'В степу.., 1964, 393); За морськими '
                                                                         'правилами, відсутність.. станового якоря не '
                                                                         'дає судну права виходити в море (Веч. Київ, '
                                                                         '28.II 1968, 4). ◊ Станови́й хребе́т: а) '
                                                                         '(заст.) те саме, що хребе́т 1; б) (чого) '
                                                                         'щось життєво важливе, найголовніше в '
                                                                         'чому-небудь. Виховання любові й поваги до '
                                                                         'праці на благо суспільства, трудове '
                                                                         'загартування людей — серцевина, становий '
                                                                         'хребет ідеологічної роботи (Ком. Укр., 1, '
                                                                         '1964, 69).',
                                                           'sovietization_risk': 1,
                                                           'keywords': ['кпрс'],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості; цитує матеріали Програми '
                                                                              'КПРС.'},
                        'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                  'quote': 'Становий, -вого, м. Становой приставь. Вони були становими '
                                                           'в одному стані. Грин. ІІ. 332.',
                                                  'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                     'Борисом Грінченком в умовах дії антиукраїнських '
                                                                     'імперських указів (Валуєвського циркуляра 1863 '
                                                                     'р. та Емського указу 1876 р.).'}}],
    'степний': [   {   'headword': 'сте́пний',
                       'short_label': 'степовий, притаманний широкому степу (нар.-поет., фольк.)',
                       'gloss': 'steppe, prairial (folk-poetic, authentic)',
                       'pos': 'adj',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[ˈstɛpnɪj]'},
                       'stress': {'form': 'сте́пний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/степний'},
                       'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                       'distinction_note': 'Поетична й народнопісенна форма до «степовий» («степний вітер, орел '
                                           'степний»). Не плутати з акцентним варіантом «степни́й».',
                       'meaning': {'definitions': ['Те саме, що степови́й (народнопоетичне).'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'СТЕ́ПНИЙ, а, е, розм. Те саме, що здíбний. — '
                                                                        'Старша дочка ваша і гарна, й здатна, й добра, '
                                                                        'і до всього степна (Н.-Лев., І, 1956, 134).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None},
                   {   'headword': 'степни́й',
                       'short_label': 'степовий (діал., фольк., варіантний кінцевий наголос)',
                       'gloss': 'steppe-dwelling, wild steppe (dialectal/folk, end-stressed)',
                       'pos': 'adj',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[stɛpˈnɪj]'},
                       'stress': {'form': 'степни́й', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/степний'},
                       'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                       'distinction_note': 'Кінцевонаголошений варіант у діалектному та пісенному вжитку. Не плутати з '
                                           'кореневим наголосом «сте́пний».',
                       'meaning': {'definitions': ['Те саме, що степови́й (варіантний наголос).'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'СТЕПНИ́Й, а́, е́, рідко. Те саме, що '
                                                                        'степови́й. А навколо багать — '
                                                                        'Куховарки-подруги, І вони гомонять Про степні '
                                                                        'лісосмуги (Криж., Срібне весілля, 1957, 307).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None}],
    'стовпище': [   {   'headword': 'сто́впище',
                        'short_label': 'велике скупчення людей, збіговисько, натовп',
                        'gloss': 'dense crowd, throng, mob, gathering of people',
                        'pos': 'noun',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈstɔu̯pɪʃt͡ʃɛ]'},
                        'stress': {'form': 'сто́впище', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/стовпище'},
                        'morphology': {   'pos': 'іменник',
                                          'paradigm': {   'kind': 'noun',
                                                          'gender': 'середній',
                                                          'cases': {   'називний': {   'singular': 'сто́впище',
                                                                                       'plural': 'сто́впища'},
                                                                       'родовий': {   'singular': 'сто́впища',
                                                                                      'plural': 'сто́впищ'},
                                                                       'давальний': {   'singular': 'сто́впищу',
                                                                                        'plural': 'сто́впищам'},
                                                                       'знахідний': {   'singular': 'сто́впище',
                                                                                        'plural': 'сто́впища'},
                                                                       'орудний': {   'singular': 'сто́впищем',
                                                                                      'plural': 'сто́впищами'},
                                                                       'місцевий': {   'singular': 'сто́впищі',
                                                                                       'plural': 'сто́впищах'},
                                                                       'кличний': {   'singular': 'сто́впище',
                                                                                      'plural': 'сто́впища'}}}},
                        'distinction_note': 'Означає густий натовп або велике безладне скупчення людей на вулиці чи '
                                            'площі. Не плутати зі збільшувальним до стовпа «стовпи́ще».',
                        'meaning': {'definitions': ['Велике скупчення людей; натовп, збіговисько.'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СТО́ВПИЩЕ, а, с. Безладне скупчення великої '
                                                                         'кількості людей; натовп. Нещасливі '
                                                                         'стовпились коло багаття.. Коли це '
                                                                         'несподівано з того стовпища сміливо виступив '
                                                                         'один старий дідуган (Н.-Лев., VII, 1966, '
                                                                         '168); Там, де ясно шугало вгору полум’я, '
                                                                         'чути було невгавний поплутаний галас '
                                                                         'людського стовпища (Гр., II, 1963, 294); '
                                                                         'Вартові.. суворо поглядали на стовпище селян '
                                                                         '(Досв., Гюлле, 1961, 57); // перен. Велика '
                                                                         'кількість кого-, чого-небудь, зосереджена в '
                                                                         'одному місці. Цілі стовпища куряви застилали '
                                                                         'світ (Л. Укр., III, 1952, 604); Білі '
                                                                         'довгасті пасма, одірвавшись од ніби '
                                                                         'нерухомого, а насправді неспокійного '
                                                                         'стовпища хмар, летять назустріч літакові '
                                                                         '(Перв., Дикий мед, 1963, 3); Раз він '
                                                                         'натрапив на цілий табун вепрів.., але не '
                                                                         'став гнатись за ними, бо стикатись одному з '
                                                                         'цілим стовпищем цих хижих звірів було '
                                                                         'небезпечно (Скл., Святослав, 1959, 14).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                  'quote': 'Стовпище, -ща, с. Толпа. Черк. у.',
                                                  'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                     'Борисом Грінченком в умовах дії антиукраїнських '
                                                                     'імперських указів (Валуєвського циркуляра 1863 '
                                                                     'р. та Емського указу 1876 р.).'}},
                    {   'headword': 'стовпи́ще',
                        'short_label': 'величезний, товстий або масивний стовп (збільш. до стовп)',
                        'gloss': 'massive post, huge pillar, oversized column (augmentative)',
                        'pos': 'noun',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[stɔu̯ˈpɪʃt͡ʃɛ]'},
                        'stress': {'form': 'стовпи́ще', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/стовпище'},
                        'morphology': {   'pos': 'іменник',
                                          'paradigm': {   'kind': 'noun',
                                                          'gender': 'середній',
                                                          'cases': {   'називний': {   'singular': 'стовпи́ще',
                                                                                       'plural': 'стовпи́ща'},
                                                                       'родовий': {   'singular': 'стовпи́ща',
                                                                                      'plural': 'стовпи́щ'},
                                                                       'давальний': {   'singular': 'стовпи́щу',
                                                                                        'plural': 'стовпи́щам'},
                                                                       'знахідний': {   'singular': 'стовпи́ще',
                                                                                        'plural': 'стовпи́ща'},
                                                                       'орудний': {   'singular': 'стовпи́щем',
                                                                                      'plural': 'стовпи́щами'},
                                                                       'місцевий': {   'singular': 'стовпи́щі',
                                                                                       'plural': 'стовпи́щах'},
                                                                       'кличний': {   'singular': 'стовпи́ще',
                                                                                      'plural': 'стовпи́ща'}}}},
                        'distinction_note': 'Збільшувально-підсилювальна форма до іменника стовп (гігантська підпора '
                                            'чи колона). Не плутати зі збіговиськом людей «сто́впище».',
                        'meaning': {'definitions': ['Збільшувальне до стовп; великий стовп.'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СТОВПИ́ЩЕ, а, с. Збільш. до стовп 1, 2.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'стожище': [   {   'headword': 'сто́жище',
                       'short_label': 'місце, де ставлять або стояли стоги сіна чи соломи; стіговище',
                       'gloss': 'haystack ground, rick-yard, place where stacks stand',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[ˈstɔʒɪʃt͡ʃɛ]'},
                       'stress': {'form': 'сто́жище', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/стожище'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'середній',
                                                         'cases': {   'називний': {   'singular': 'сто́жище',
                                                                                      'plural': 'сто́жища'},
                                                                      'родовий': {   'singular': 'сто́жища',
                                                                                     'plural': 'сто́жищ'},
                                                                      'давальний': {   'singular': 'сто́жищу',
                                                                                       'plural': 'сто́жищам'},
                                                                      'знахідний': {   'singular': 'сто́жище',
                                                                                       'plural': 'сто́жища'},
                                                                      'орудний': {   'singular': 'сто́жищем',
                                                                                     'plural': 'сто́жищами'},
                                                                      'місцевий': {   'singular': 'сто́жищі',
                                                                                      'plural': 'сто́жищах'},
                                                                      'кличний': {   'singular': 'сто́жище',
                                                                                     'plural': 'сто́жища'}}}},
                       'distinction_note': "Локативне значення: поле чи ділянка подвір'я, де зводять стоги "
                                           '(стіговище). Не плутати з величезним стогом «стожи́ще».',
                       'meaning': {'definitions': ['Місце, де стоять або стояли стоги.'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'СТО́ЖИЩЕ, а, с. Підкладка, підстилка під стіг '
                                                                        'для збереження його від сирості знизу; '
                                                                        'підстіжжя.',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None},
                   {   'headword': 'стожи́ще',
                       'short_label': 'величезний, велетенський стіг сіна або хліба (збільш. до стіг)',
                       'gloss': 'gigantic haystack, massive grain stack (augmentative)',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[stɔˈʒɪʃt͡ʃɛ]'},
                       'stress': {'form': 'стожи́ще', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/стожище'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'середній',
                                                         'cases': {   'називний': {   'singular': 'стожи́ще',
                                                                                      'plural': 'стожи́ща'},
                                                                      'родовий': {   'singular': 'стожи́ща',
                                                                                     'plural': 'стожи́щ'},
                                                                      'давальний': {   'singular': 'стожи́щу',
                                                                                       'plural': 'стожи́щам'},
                                                                      'знахідний': {   'singular': 'стожи́ще',
                                                                                       'plural': 'стожи́ща'},
                                                                      'орудний': {   'singular': 'стожи́щем',
                                                                                     'plural': 'стожи́щами'},
                                                                      'місцевий': {   'singular': 'стожи́щі',
                                                                                      'plural': 'стожи́щах'},
                                                                      'кличний': {   'singular': 'стожи́ще',
                                                                                     'plural': 'стожи́ща'}}}},
                       'distinction_note': 'Збільшувальна форма від стіг: стіг велетенських розмірів. Не плутати з '
                                           'місцем розташування стогів «сто́жище».',
                       'meaning': {'definitions': ['Збільшувальне до стіг; дуже великий стіг.'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'СТОЖИ́ЩЕ, а, ч. Збільш. до стіг.',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None}],
    'струхнути': [   {   'headword': 'стру́хнути',
                         'short_label': 'струхлявіти, згнити, розсипатися на порохню (док., розм.)',
                         'gloss': 'rot away, decay into dust, crumble from rot (perf., colloq.)',
                         'pos': 'verb',
                         'cefr': 'B2',
                         'heritage_status': {   'classification': 'standard',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True},
                         'pronunciation': {'ipa': '[ˈstruxnutɪ]'},
                         'stress': {   'form': 'стру́хнути',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/струхнути'},
                         'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                         'distinction_note': 'Означає струхлявіти, зотліти або перетворитися на трухлявину. Не плутати '
                                             'з різким струшуванням чи потрушуванням «струхну́ти».',
                         'meaning': {   'definitions': ['Те саме, що струхлявіти; згнити, розсипатися на порохню.'],
                                        'source': 'ВТС'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СТРУ́ХНУТИ, не, док., розм. Те саме, що '
                                                                          'струхля́віти. *Образно. — Я знаю, що ваші '
                                                                          'дукати і струхнуть при вас! — спалахнула '
                                                                          'панночка (Л. Янов., I, 1959, 121).',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                   'quote': 'Струхнути 2, -хну, -неш, гл. Сгнить. Корінь його струхне. '
                                                            'К. Іов. 30. Галя може струхла там у землі. Рудч. Ск. І. '
                                                            '138.',
                                                   'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                      'Борисом Грінченком в умовах дії антиукраїнських '
                                                                      'імперських указів (Валуєвського циркуляра 1863 '
                                                                      'р. та Емського указу 1876 р.).'}},
                     {   'headword': 'струхну́ти',
                         'short_label': 'струснути, скинути різким струсом або потрусити (док., рідко)',
                         'gloss': 'shake off, jerk, shake or toss with a quick movement (perf., rare)',
                         'pos': 'verb',
                         'cefr': 'B2',
                         'heritage_status': {   'classification': 'standard',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True},
                         'pronunciation': {'ipa': '[struxˈnutɪ]'},
                         'stress': {   'form': 'струхну́ти',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/струхнути'},
                         'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                         'distinction_note': 'Означає скинути струсом або різко струснути (струхнути сигарету, '
                                             'струхнути іній). Не плутати з гниттям деревини «стру́хнути».',
                         'meaning': {   'definitions': ['Те саме, що струснути; скинути або струснути різким рухом.'],
                                        'source': 'ВТС'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СТРУХНУ́ТИ, ну́, не́ш, док., перех. і '
                                                                          'неперех., рідко. Те саме, що струсну́ти. '
                                                                          'Слідчий Руллер.. однією рукою струхнув нову '
                                                                          'сигарету об підставку розп’яття (Гашек, '
                                                                          'Пригоди.. Швейка, перекл. Масляка, 1958, '
                                                                          '329); Гостре лезо лягло в розсішок яблуні, '
                                                                          'струхнувши іній (Шиян, Переможці, 1950, '
                                                                          '83); — Хай вас чорт візьме всіх! — '
                                                                          'струхнувши очіпком, грубо кинула Настя '
                                                                          '(Вас., І, 1959, 286).',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                   'quote': 'Струхнути, -хну, -неш, гл. = струснути. Коли б струхнув '
                                                            'хоть головою. Котл. Ен. II. 31.',
                                                   'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                      'Борисом Грінченком в умовах дії антиукраїнських '
                                                                      'імперських указів (Валуєвського циркуляра 1863 '
                                                                      'р. та Емського указу 1876 р.).'}}],
    'сунутися': [   {   'headword': 'су́нутися',
                        'short_label': 'рухатися повільно, повзти всією масою або пересуватися (недок.)',
                        'gloss': 'move slowly, creep forward, advance in bulk (imperf.)',
                        'pos': 'verb',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈsunutɪsʲɐ]'},
                        'stress': {'form': 'су́нутися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сунутися'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                        'distinction_note': 'Означає повільно або суцільною масою посуватися вперед (хмари сунуться, '
                                            'віз сунеться). Не плутати з недоречним утручанням «суну́тися».',
                        'meaning': {'definitions': ['Повільно рухатися, посуватися вперед.'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СУ́НУТИСЯ, нуся, нешся, недок. 1. Іти, '
                                                                         'рухатися, пересуватися, перев. повільно або '
                                                                         'через силу. Помаленьку й повагом — не йшов, '
                                                                         'а неначе сунувся Бичковський до стола, де '
                                                                         'сиділи гості (Н.-Лев., VI, 1966, 35); Сани '
                                                                         'ледве сунулись (Мик., II, 1957, 282); Ви '
                                                                         'бачили, як сунеться машина, Вантажена '
                                                                         'камінням і залізом? Горять, курять масні '
                                                                         'широкі шини, Двигун з напруги крекче: '
                                                                         '«Лізем, лізем» (Воронько, Коли я.., 1962, '
                                                                         '94); *У порівн. Круг них усе їжився '
                                                                         'височенний, цупкий, жовтий комиш, немов '
                                                                         'сунувся разом із ними, як зачарований '
                                                                         '(Коцюб., І, 1955, 360); // Наближатися до '
                                                                         'кого-, чого-небудь; насуватися. Бійцям '
                                                                         'уявлялися.. ворожі гуркітливі танки, що '
                                                                         'сунуться на них, як сліпі, незграбні потвори '
                                                                         '(Гончар, III, 1959, 36); Навала сунулася, як '
                                                                         'чума, невмолима й жорстока (Ле, Ю. Кудря, '
                                                                         '1956. 6); // Відходити, відступати від '
                                                                         'кого-, чого-небудь. Німці сунуться назад '
                                                                         '(Нагн., Пісня.., 1949, 45); *Образно. Стовпи '
                                                                         'сунулись назад. Пил дорожній віявся хвостом '
                                                                         '(Ю. Янов., І, 1958, 67); // Рухатися великою '
                                                                         'масою, безперервним потоком. Скільки оком '
                                                                         'кинеш — скрізь по дорозі, як гадюка, '
                                                                         'сунуться хури (Стор., І, 1957, 77); Ми лише '
                                                                         'бачили, що юрма сунеться в наш бік (Коцюб., '
                                                                         'І, 1955, 256); Мова йшла про безперестанний '
                                                                         'потік німецьких санітарних ешелонів, що '
                                                                         'сунулись зі сходу через дарницький міст (Д. '
                                                                         'Бедзик, Дніпро.., 1951, 32); // Змінювати '
                                                                         'своє положення в просторі. [Мавка:] Сунеться '
                                                                         'хмарка по небу повільна… (Л. Укр., III, '
                                                                         '1952, 256); Сонце сунулось вище і вище, '
                                                                         'Починалися перші жнива (Мас., Побратими, '
                                                                         '1950, 181); Зголубіли зимні шиби, Пролетіли '
                                                                         'птиці сонні, Заспокоїлися кроки… Тіні '
                                                                         'сунуться широкі (Рильський, II, 1960, 50); З '
                                                                         'долини од річки, як гурт сірих волів, '
                                                                         'сунувся туман (Головко, І, 1957, 81); // '
                                                                         'перен., рідко. Повільно минати (про час). '
                                                                         'Осінній день сунеться поволі (Коцюб., І, '
                                                                         '1955, 367). 2. Соваючись, наближатися до '
                                                                         'кого-, чого-небудь; підсуватися. Грицько '
                                                                         'мерщій посунувся за стіл, на покуття, та '
                                                                         'запрохував Чіпку сунутись ближче до його '
                                                                         '(Мирний, І, 1949, 273); — Сунься ближче до '
                                                                         'мене… (Гончар, II, 1959, 368). ◊ Су́нутися '
                                                                         'під ру́ку (ру́ки) — те саме, що '
                                                                         'Підверта́тися (попада́ти, попада́тися, '
                                                                         'потрапля́ти, трапля́тися і т. ін.) під ру́ку '
                                                                         '(ру́ки) ( див. рука́). Брала [Домніка] все, '
                                                                         'що сунулося під руку, — збіжжя, насіння, '
                                                                         'хатні знаряди (Коб., II, 1956, 123). 3. Не '
                                                                         'втримавшись де-небудь, повільно сповзати або '
                                                                         'скочуватися вниз по похилій поверхні; '
                                                                         'зсовуватися. Гора така крута, так і сунуться '
                                                                         'ноги (Мирний, III, 1954, 298); Схил був '
                                                                         'крутий, і люди не йшли, а сунулися з нього '
                                                                         '(Тют., Вир, 1964, 314); Вугілля само '
                                                                         'сунулось в риштак, вливаючись у загальний '
                                                                         'потік антрациту на конвейєр (Донч., Шахта.., '
                                                                         '1949, 123); // Сповзати, злазити з '
                                                                         'чого-небудь на землю, підлогу і т. ін. Не '
                                                                         'втерпів дід. Заворушився.., закашляв і '
                                                                         'вперше за тиждень почав сунутися з печі '
                                                                         '(Кир., Вибр., 1960, 356); // Посуваючись, '
                                                                         'переміщатися на певну відстань від кого-, '
                                                                         'чого-небудь; відсуватися. Враз почув [дід], '
                                                                         'що його торба кудись сунеться, що її вже '
                                                                         'нема! (Коцюб., І, 1955, 134). 4. розм. '
                                                                         'Намагатися проникнути, потрапити '
                                                                         'куди-небудь. Виряджала в доріженьку Мати '
                                                                         'свого сина. Виряджала, промовляла: — Сину '
                                                                         'мій коханий, Дивись пильно, щоб не сунувсь '
                                                                         'Ворог препоганий (Укр.. лір. пісні, 1958, '
                                                                         '593); [Олімпіада Іванівна (побачивши '
                                                                         'дітей):] Ви сюди як влізли? [Xлопчик:] Там '
                                                                         'не зачинено… [Олімпіада Іванівна:] Ох, уже '
                                                                         'мені сі літні виходи! А ви ж чого сунетесь '
                                                                         'сюди, що ж, що не зачинено, то вам уже й '
                                                                         'треба? (Л. Укр., II, 1951, 19); Я йому не '
                                                                         'раз казав — не лізь даремно під кулі, не '
                                                                         'сунься у воду, не питавши броду (Збан., '
                                                                         'Доля, 1961, 109); // Звертатися до '
                                                                         'кого-небудь проти його бажання, надокучати '
                                                                         'комусь. Я ввійшла, а пані: — Чого сунешся? '
                                                                         '(Вовчок, І, 1955, 123); // Втручатися в чужі '
                                                                         'справи. Ганна з затиснутим револьвером у '
                                                                         'руці кинулась у саму гущу бандитів: — Не '
                                                                         'смійте! Припиніть дітовбивство! — Хтось '
                                                                         'грубо відштовхнув її..: — Не сунься, '
                                                                         'отаманко, не в своє! (Гончар, II, 1959, '
                                                                         '264); // зневажл. Намагатися досягти певного '
                                                                         'становища, прагнути стати ким-небудь '
                                                                         'значущим. Не хочеш страти, — не сунься ні в '
                                                                         'куми, ні в свати! (Номис, 1864, № 9498). ◊ '
                                                                         'Су́нутися попере́д ба́тька в пе́кло — те '
                                                                         'саме, що Лі́зти попере́д ба́тька в пе́кло ( '
                                                                         'див. лі́зти) — Але ж ви, діду, таки щось '
                                                                         'заробляли? — Постривай-бо, не сунься поперед '
                                                                         'батька в пекло! Заробляли… (Н.-Лев., І, '
                                                                         '1956, 56). 5. Пас. до су́нути 1, 2. Усі ті '
                                                                         'професори вийшли буцімто випадком в світлицю '
                                                                         'й попрямували до стола тихою рівною ступою, '
                                                                         'неначе червонясті ляльки сунулись чиєюсь '
                                                                         'захованою потайною рукою (Н.-Лев., VII, '
                                                                         '1966, 15).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                  'quote': 'Сунутися 1, -нуся, -нешся, гл. 1) Соваться. Не питаючи '
                                                           'броду, не сунься у воду. Ном. 2) Медленно двигаться, '
                                                           'надвигаться. Стрічкою сунулись козаки. Стор. МПр. 124.',
                                                  'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                     'Борисом Грінченком в умовах дії антиукраїнських '
                                                                     'імперських указів (Валуєвського циркуляра 1863 '
                                                                     'р. та Емського указу 1876 р.).'}},
                    {   'headword': 'суну́тися',
                        'short_label': 'лізти, пхатися кудись недоречно, утручатися в чужі справи (розм.)',
                        'gloss': "meddle, poke one's nose, push into unwelcoming places (colloq.)",
                        'pos': 'verb',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[suˈnutɪsʲɐ]'},
                        'stress': {'form': 'суну́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сунутися'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                        'distinction_note': 'Експресивне позначення настирливого або недоречного вторгнення («не '
                                            'сунься у воду, не знаючи броду»). Не плутати з повільним рухом '
                                            '«су́нутися».',
                        'meaning': {   'definitions': ['Лізти, потикатися кудись без потреби; утручатися.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'СУНУ́ТИСЯ, ну́ся, не́шся, док. 1. Кинутися '
                                                                         'до кого-, чого-небудь. — Лупурелло вдарив '
                                                                         'офіцера палицею. Тоді всі офіцери сунулись '
                                                                         'до Лупурелла, добре попобили (Н.-Лев., V, '
                                                                         '1966, 143); — Брешшеш! — засичала Пріська, '
                                                                         'знову сунувшись до Грицька (Мирний, III, '
                                                                         '1954, 125); // Ураз побігти, понестися '
                                                                         'куди-небудь (перев. про багатьох). Не швидко '
                                                                         'бідні [вельможі] схаменулись І в ратуш '
                                                                         '[ратушу] підтюпцем сунулись. Уже як вечір '
                                                                         'наступив (Котл., І, 1952, 186); — Як князь '
                                                                         'проїде й нарід [народ] сунеться за коляскою, '
                                                                         'ми з тобою підемо у степ і там десь '
                                                                         'пересидимо у балці (Хотк., І, 1966, 108); // '
                                                                         'Спрямувати свій інтерес на кого-, що-небудь. '
                                                                         'Від ласощів аж віття гнуться, Не знаєш, до '
                                                                         'чого й сунуться: — Мигдалики і виноград, — '
                                                                         'їси, їси, аж рад (Гл., Вибр., 1951, 75); // '
                                                                         'Потрапити куди-небудь через власну '
                                                                         'необачність. Із дверей мов лихий пхнув '
                                                                         'жінку, трохи коневі під ноги не сунулась (П. '
                                                                         'Куліш, Вибр., 1969, 119); Один із '
                                                                         'зголоднілих птахів сунувся мені просто в '
                                                                         'руки (Сенч., Опов., 1959, 294). 2. розм. '
                                                                         'Прийти, прибути, з’явитися куди-небудь; '
                                                                         'поткнутися. [Xорунжий:] Нехай тільки '
                                                                         'сунеться [Гаркуша], то ми його на першій '
                                                                         'осиці провітримо! (Стор., І, 1957, 293); '
                                                                         'Сунулись були туди раз і качки, але їм '
                                                                         'такого перепало від учителя, що вони.. того '
                                                                         'часу обминають ставок десятою дорогою '
                                                                         '(Донч., І, 1956, 51); // у сполуч. із інфін. '
                                                                         'Спробувати що-небудь зробити. З троянди '
                                                                         'квіточку Івась сунувсь зірвать (Бор., Тв., '
                                                                         '1957, 186); Я [цибуля] сердита зроду: Хто '
                                                                         'задивиться на вроду Чи сунеться цілувать — '
                                                                         'Буде сльози проливать (Гл., Вибр., 1951, '
                                                                         '216); // Зробити спробу влаштуватися '
                                                                         'куди-небудь працювати, вчитися і т. ін.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'сушений': [   {   'headword': 'су́шений',
                       'short_label': 'який зазнав процесу сушіння, висушений (дієприкметник)',
                       'gloss': 'dried, desiccated through a process of drying (participle)',
                       'pos': 'adj',
                       'cefr': 'A2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[ˈsuʃɛnɪj]'},
                       'stress': {'form': 'су́шений', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сушений'},
                       'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                       'distinction_note': 'Дієприкметникова форма від дієслова сушити (акцент на самій дії сушіння). '
                                           'Не плутати з якісним харчовим прикметником «суше́ний».',
                       'meaning': {   'definitions': ['Дієприкметник пасивного стану минулого часу до сушити.'],
                                      'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'СУ́ШЕНИЙ, а, е. Дієпр. пас. мин. ч. до '
                                                                        'суши́ти.',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None},
                   {   'headword': 'суше́ний',
                       'short_label': 'заготовлений способом сушіння (про продукти: гриби, фрукти)',
                       'gloss': 'dried (fruits, mushrooms, fish; food adjective)',
                       'pos': 'adj',
                       'cefr': 'A2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[suˈʃɛnɪj]'},
                       'stress': {'form': 'суше́ний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/сушений'},
                       'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                       'distinction_note': 'Якісний прикметник: приготований як сухий продукт для тривалого зберігання '
                                           '(«сушені гриби, сушені яблука, сушена риба»). Не плутати з дієприкметником '
                                           'дії «су́шений».',
                       'meaning': {'definitions': ['Приготовлений, заготовлений способом сушіння.'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'СУШЕ́НИЙ, а, е. Зготовлений сушінням, '
                                                                        'в’яленням. Якщо сушені плоди та ягоди '
                                                                        'залишаються довго на повітрі, вони вбирають '
                                                                        'вологу і псуються (Сад. і ягідн., 1957, 285); '
                                                                        'Жінка поставила перед ним миску холодного '
                                                                        'борщу з сушеною рибою (Збан., Таємниця.., '
                                                                        '1971, 170); У хаті в діда Дениса — чисто.. '
                                                                        'Пахло бруньками й грибами. В’язки сушених '
                                                                        'грибів — у запічку (Мушк., День.., 1967, 54); '
                                                                        'В коморі пахло борошном і сушеним липовим '
                                                                        'цвітом (Тют., Вир, 1964, 47).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None}],
    'схрипнути': [   {   'headword': 'схри́пнути',
                         'short_label': 'стати хрипким, захрипнути від крику або застуди (док.)',
                         'gloss': 'become hoarse, lose clear voice through shouting or cold (perf.)',
                         'pos': 'verb',
                         'cefr': 'B2',
                         'heritage_status': {   'classification': 'standard',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True},
                         'pronunciation': {'ipa': '[ˈsxrɪpnutɪ]'},
                         'stress': {   'form': 'схри́пнути',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/схрипнути'},
                         'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                         'distinction_note': 'Означає втратити чистоту голосу (голос схрип). Не плутати з варіантним '
                                             'кінцевим наголосом «схрипну́ти».',
                         'meaning': {'definitions': ['Втратити чистоту голосу, стати охриплим.'], 'source': 'ВТС'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СХРИ́ПНУТИ, ну, неш; мин. ч. схрип і '
                                                                          'схри́пнув, ла, ло; док., розм. Те саме, що '
                                                                          'охри́пнути. Голоси схрипли від напруження, '
                                                                          'порохні, вигуків (Коп., Вибр., 1948, 124).',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': None},
                     {   'headword': 'схрипну́ти',
                         'short_label': 'захрипнути, втратити дзвінкість голосу (варіантний наголос)',
                         'gloss': 'turn raspy, hoarsen (variant stress)',
                         'pos': 'verb',
                         'cefr': 'B2',
                         'heritage_status': {   'classification': 'standard',
                                                'is_russianism': False,
                                                'russian_shadow': False,
                                                'vesum_attested': True},
                         'pronunciation': {'ipa': '[sxrɪpˈnutɪ]'},
                         'stress': {   'form': 'схрипну́ти',
                                       'source': 'ВТС',
                                       'url': 'https://slovnyk.me/dict/vts/схрипнути'},
                         'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                         'distinction_note': 'Кінцевонаголошений варіант до дієслова схрипнути. Не плутати з '
                                             'нормативним кореневим «схри́пнути».',
                         'meaning': {'definitions': ['Те саме, що схри́пнути (варіант наголосу).'], 'source': 'ВТС'},
                         'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                            'definition': 'СХРИПНУ́ТИ, ну́, не́ш, док. Однокр. до '
                                                                          'схри́пувати.',
                                                            'sovietization_risk': 0,
                                                            'keywords': [],
                                                            'historical_note': 'Зафіксовано в радянський період '
                                                                               '(СУМ-11). Наведено для '
                                                                               'лексикографічної прозорості.'},
                         'pre_soviet_witness': None}],
    'тамбур': [   {   'headword': 'та́мбур',
                      'short_label': 'закритий майданчик пасажирського вагона або вхідний шлюз будівлі',
                      'gloss': 'vestibule, entrance platform of railway carriage, airlock foyer',
                      'pos': 'noun',
                      'cefr': 'B1',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[ˈtɑmbur]'},
                      'stress': {'form': 'та́мбур', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тамбур'},
                      'morphology': {   'pos': 'іменник',
                                        'paradigm': {   'kind': 'noun',
                                                        'gender': 'чоловічий',
                                                        'cases': {   'називний': {   'singular': 'та́мбур',
                                                                                     'plural': 'та́мбури'},
                                                                     'родовий': {   'singular': 'та́мбура',
                                                                                    'plural': 'та́мбурів'},
                                                                     'давальний': {   'singular': 'та́мбуру / '
                                                                                                  'та́мбурові',
                                                                                      'plural': 'та́мбурам'},
                                                                     'знахідний': {   'singular': 'та́мбур',
                                                                                      'plural': 'та́мбури'},
                                                                     'орудний': {   'singular': 'та́мбуром',
                                                                                    'plural': 'та́мбурами'},
                                                                     'місцевий': {   'singular': 'та́мбурі',
                                                                                     'plural': 'та́мбурах'},
                                                                     'кличний': {   'singular': 'та́мбуре',
                                                                                    'plural': 'та́мбури'}}}},
                      'distinction_note': 'Транспортний і архітектурний термін: сіни вагона або прибудова при вході '
                                          'для захисту від холоду. Не плутати з вишивальним швом чи барабаном '
                                          '«тамбу́р».',
                      'meaning': {   'definitions': [   'Закритий майданчик залізничного вагона біля вхідних дверей; '
                                                        'прибудова біля входу в будівлю.'],
                                     'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'ТА́МБУР, а, ч. 1. Прибудова біля входу в '
                                                                       'приміщення; сіни. При вході до будинку або в '
                                                                       'самій роздягальні повинен бути тамбур, завдяки '
                                                                       'якому, коли відчинять зовнішні двері, холодне '
                                                                       'повітря не проникає до вестибюля, де '
                                                                       'роздягаються діти, а спочатку змішується з '
                                                                       'нагрітим повітрям тамбура (Шк. гігієна, 1954, '
                                                                       '180); Зібравшись біля бокового тамбура, де '
                                                                       'зберігалися всякі доярські причандали, доярки '
                                                                       'перешіптувались (Добр., Тече річка.., 1961, '
                                                                       '29). 2. Закритий майданчик пасажирського '
                                                                       'залізничного вагона. Він стояв у тамбурі,.. '
                                                                       'нетерпляче чекаючи хвилини, коли поїзд '
                                                                       'зупиниться (Рибак, Час.., 1960, 771); Микола '
                                                                       'Щорс стояв на східцях вагона, поки поїзд не '
                                                                       'рушив від станції, а тоді ступив у тамбур '
                                                                       'вагона (Скл., Легенд. начдив, 1957, 16). 3. '
                                                                       'архт. Те саме, що бараба́н 3. ТА́МБУР², а, ч. '
                                                                       'Вид вишивання або плетіння, коли кожна '
                                                                       'наступна петля нитки протягається гачком або '
                                                                       'голкою через попередню.',
                                                         'sovietization_risk': 0,
                                                         'keywords': [],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної '
                                                                            'прозорості.'},
                      'pre_soviet_witness': None},
                  {   'headword': 'тамбу́р',
                      'short_label': "ланцюжковий вишивальний шов або круглі п'яльця для вишивання (спец.)",
                      'gloss': 'tambour embroidery stitch, tambour frame; hist. drum',
                      'pos': 'noun',
                      'cefr': 'B2',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[tɐmˈbur]'},
                      'stress': {'form': 'тамбу́р', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тамбур'},
                      'morphology': {   'pos': 'іменник',
                                        'paradigm': {   'kind': 'noun',
                                                        'gender': 'чоловічий',
                                                        'cases': {   'називний': {   'singular': 'тамбу́р',
                                                                                     'plural': 'тамбу́ри'},
                                                                     'родовий': {   'singular': 'тамбу́ра',
                                                                                    'plural': 'тамбу́рів'},
                                                                     'давальний': {   'singular': 'тамбу́ру / '
                                                                                                  'тамбу́рові',
                                                                                      'plural': 'тамбу́рам'},
                                                                     'знахідний': {   'singular': 'тамбу́р',
                                                                                      'plural': 'тамбу́ри'},
                                                                     'орудний': {   'singular': 'тамбу́ром',
                                                                                    'plural': 'тамбу́рами'},
                                                                     'місцевий': {   'singular': 'тамбу́рі',
                                                                                     'plural': 'тамбу́рах'},
                                                                     'кличний': {   'singular': 'тамбу́ре',
                                                                                    'plural': 'тамбу́ри'}}}},
                      'distinction_note': "Мистецький термін: особливий шов петельками (ланцюжком) або п'яльця "
                                          '(вишивати тамбуром; муз. старовинний барабан). Не плутати з тамбуром вагона '
                                          '«та́мбур».',
                      'meaning': {   'definitions': ["Особливий шов для вишивання у вигляді ланцюжка; круглі п'яльця."],
                                     'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'ТАМБУ́Р, а, ч., муз., заст. Барабан (у 1 '
                                                                       'знач.).',
                                                         'sovietization_risk': 0,
                                                         'keywords': [],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної '
                                                                            'прозорості.'},
                      'pre_soviet_witness': None}],
    'танковий': [   {   'headword': 'та́нковий',
                        'short_label': 'стосовний до броньованої бойової машини — танка (військ.)',
                        'gloss': 'tank-related, armored, panzer (military)',
                        'pos': 'adj',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈtɑnkɔwɪj]'},
                        'stress': {'form': 'та́нковий', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/танковий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Військовий термін: стосовний до бойового танка (танкові війська, танкова '
                                            'броня, танковий взвод). Не плутати з народним хороводним танцем '
                                            '«танко́вий».',
                        'meaning': {'definitions': ['Прикметник до танк (бойова броньована машина).'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ТА́НКОВИЙ, а, е. 1. Прикм. до танк¹. Хоч '
                                                                         'немало бійців полягло від танкового вогню.., '
                                                                         'артилеристи знищили ще шість танків і цим '
                                                                         'врятували фланг (Довж., І, 1958, 286); Чути '
                                                                         'гудіння танкового мотора (Собко, П’єси, '
                                                                         '1958, 62); // Оснащений танками; який '
                                                                         'складається з танків. Коли танкова колона на '
                                                                         'хвилину чомусь спинилася, я непомітно '
                                                                         'видерся на броню величезного танка (Сміл., '
                                                                         'Сашко, 1954, 207); Танкові війська; Танковий '
                                                                         'корпус; // Який виробляє танки. Танкова '
                                                                         'промисловість; // Признач. для виробництва '
                                                                         'танків. Танкова сталь; // Який здійснюється '
                                                                         'за допомогою танків. Про можливість танкової '
                                                                         'атаки на плацдарм бійці були попереджені '
                                                                         'заздалегідь (Гончар, II, 1959, 375); '
                                                                         'Танковий бій мій генерал провадить на '
                                                                         'скаженому темпі (Ю. Янов., І, 1958, 341). 2. '
                                                                         'Який готує танкістів. Танкове училище.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'та́нко́вий',
                        'short_label': 'стосовний до народного танцю, хороводу або танкових співів (фольк.)',
                        'gloss': 'dance-related, folk-dance, choreographic (folk-music)',
                        'pos': 'adj',
                        'cefr': 'B2',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[tɐnˈkɔwɪj]'},
                        'stress': {   'form': 'та́нко́вий',
                                      'source': 'ВТС',
                                      'url': 'https://slovnyk.me/dict/vts/танковий'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Фольклорний термін: прикметник до танок (танець, хоровод: танкова пісня, '
                                            'танковий крок). Не плутати з бронетехнікою «та́нковий».',
                        'meaning': {'definitions': ['Прикметник до танок (танець, хоровод).'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ТА́НКОВИ́Й, о́ва́, о́ве́. Прикм. до тано́к. '
                                                                         'Танкова гра; Танкові рухи; // Власт. '
                                                                         'танкові. Покута не переставав молитися. Але '
                                                                         'щодалі поклони його все більше й більше '
                                                                         'наближалися до танкового ритму (Панч, Гомон. '
                                                                         'Україна, 1954, 100); // Признач. для танку. '
                                                                         'Танкова музика.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'темник': [   {   'headword': 'те́мник',
                      'short_label': 'закрита директива чи інструкція цензури для ЗМІ (політ., публ.)',
                      'gloss': 'editorial directive, censorship guidance memorandum (politics, media)',
                      'pos': 'noun',
                      'cefr': 'B2',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[ˈtɛmnɪk]'},
                      'stress': {'form': 'те́мник', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/темник'},
                      'morphology': {   'pos': 'іменник',
                                        'paradigm': {   'kind': 'noun',
                                                        'gender': 'чоловічий',
                                                        'cases': {   'називний': {   'singular': 'те́мник',
                                                                                     'plural': 'те́мники'},
                                                                     'родовий': {   'singular': 'те́мника',
                                                                                    'plural': 'те́мників'},
                                                                     'давальний': {   'singular': 'те́мнику / '
                                                                                                  'те́мникові',
                                                                                      'plural': 'те́мникам'},
                                                                     'знахідний': {   'singular': 'те́мник',
                                                                                      'plural': 'те́мники'},
                                                                     'орудний': {   'singular': 'те́мником',
                                                                                    'plural': 'те́мниками'},
                                                                     'місцевий': {   'singular': 'те́мнику',
                                                                                     'plural': 'те́мниках'},
                                                                     'кличний': {   'singular': 'те́мнику',
                                                                                    'plural': 'те́мники'}}}},
                      'distinction_note': 'Сучасний суспільно-політичний термін: директива авторитарної влади '
                                          'журналістам щодо тем висвітлення (політичний темник). Не плутати з темним '
                                          'льохом «темни́к».',
                      'meaning': {   'definitions': [   'Таємна інструкція, директива влади засобам масової інформації '
                                                        "щодо обов'язкового висвітлення певних тем."],
                                     'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'ТЕ́МНИК¹, а, ч., розм. Список або збірник тем '
                                                                       'для рефератів, досліджень і т. ін. Ще в 1958 '
                                                                       'році, коли на «Укркабелі» склали темник для '
                                                                       'раціоналізаторів і винахідників, включили до '
                                                                       'нього й таку тему: «Запропонуйте спосіб '
                                                                       'пофарбування лаків для одержання кольорових '
                                                                       'світлостійких лакованих дротів» (Рад. Укр., '
                                                                       '20.VІІІ 1961, 3). ТЕ́МНИК², а, ч., іст. '
                                                                       'Татарський військовий начальник, який '
                                                                       'командував десятитисячним військом. Кожне '
                                                                       'володіння повинно було давати Чингіс-ханові '
                                                                       'певну кількість воїнів. Тому володіння ці мали '
                                                                       'назви за чисельністю загонів, що вони '
                                                                       'виставляли: сотня, тисяча, тьма (десять '
                                                                       'тисяч), і васали поділялися на сотників, '
                                                                       'тисячників і темників (Іст. СРСР, І, 1956, '
                                                                       '74).',
                                                         'sovietization_risk': 1,
                                                         'keywords': ['срср'],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної прозорості; '
                                                                            'цитує радянську пресу та історичні '
                                                                            'джерела СРСР.'},
                      'pre_soviet_witness': None},
                  {   'headword': 'темни́к',
                      'short_label': 'темне приміщення, льох або тюрма; заст. темний підвал (розм.)',
                      'gloss': 'dark cellar, dungeon, dark room, lockup (colloq., arch.)',
                      'pos': 'noun',
                      'cefr': 'B2',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[tɛmˈnɪk]'},
                      'stress': {'form': 'темни́к', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/темник'},
                      'morphology': {   'pos': 'іменник',
                                        'paradigm': {   'kind': 'noun',
                                                        'gender': 'чоловічий',
                                                        'cases': {   'називний': {   'singular': 'темни́к',
                                                                                     'plural': 'темники́'},
                                                                     'родовий': {   'singular': 'темника́',
                                                                                    'plural': 'темникі́в'},
                                                                     'давальний': {   'singular': 'темнику́ / '
                                                                                                  'темнико́ві',
                                                                                      'plural': 'темника́м'},
                                                                     'знахідний': {   'singular': 'темни́к',
                                                                                      'plural': 'темники́'},
                                                                     'орудний': {   'singular': 'темнико́м',
                                                                                    'plural': 'темника́ми'},
                                                                     'місцевий': {   'singular': 'темнику́',
                                                                                     'plural': 'темника́х'},
                                                                     'кличний': {   'singular': 'темнику́',
                                                                                    'plural': 'темники́'}}}},
                      'distinction_note': 'Автентичне народне значення: підвал, темна кімната без вікон, темниця '
                                          '(«завів мене в темник»). Не плутати з медійними директивами «те́мник».',
                      'meaning': {'definitions': ["Темне приміщення, підвал або в'язниця."], 'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'ТЕМНИ́К, а́, ч., розм. Погріб, винний льох. '
                                                                       'Вона, тривожачись, тепер побоюється йти до '
                                                                       'зимарки, на другій половині якої в темнику '
                                                                       'стоїть дев’ятиденний навар із вовчого лика '
                                                                       '(Стельмах, І, 1962, 540).',
                                                         'sovietization_risk': 0,
                                                         'keywords': [],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної '
                                                                            'прозорості.'},
                      'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                'quote': 'Темник, -ка, м. Погреб? Темное помещеніе? Кучерявий мельник '
                                                         'завів мене в темник. Чуб. IV. 498.',
                                                'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                   'Борисом Грінченком в умовах дії антиукраїнських '
                                                                   'імперських указів (Валуєвського циркуляра 1863 р. '
                                                                   'та Емського указу 1876 р.).'}}],
    'товчений': [   {   'headword': 'то́вчений',
                        'short_label': 'який зазнав товчення, подрібнений дією (дієприкметник)',
                        'gloss': 'crushed, pounded, bruised by an action (passive participle)',
                        'pos': 'adj',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈtɔu̯t͡ʃɛnɪj]'},
                        'stress': {'form': 'то́вчений', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/товчений'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Дієприкметник минулого часу від товкти (фокус на здійсненні процесу: '
                                            '«товчене в ступі зерно»). Не плутати з кулінарним прикметником '
                                            '«товче́ний».',
                        'meaning': {   'definitions': ['Дієприкметник пасивного стану минулого часу до товкти́.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ТО́ВЧЕНИЙ, а, е. Дієпр. пас. мин. ч. до '
                                                                         'товкти́. Коли він заходив у кімнату, Марфа '
                                                                         'вже насипала кулешу в миску, що густо '
                                                                         'парував, заповнюючи приміщення духмяним '
                                                                         'запахом старого, товченого з цибулею і '
                                                                         'часником сала (Коп., Земля.., 1957, 157).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None},
                    {   'headword': 'товче́ний',
                        'short_label': "подрібнений або зім'ятий у кашоподібну масу (товчена картопля)",
                        'gloss': 'mashed, pulverized, crushed (mashed potatoes, crushed glass)',
                        'pos': 'adj',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[tɔu̯ˈt͡ʃɛnɪj]'},
                        'stress': {'form': 'товче́ний', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/товчений'},
                        'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                        'distinction_note': 'Постійна якісна ознака предмета чи кулінарної страви («товчена картопля, '
                                            'товчене скло, товчений часник»). Не плутати з дієприкметником дії '
                                            '«то́вчений».',
                        'meaning': {   'definitions': ["Пом'якшений або подрібнений унаслідок товчення."],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ТОВЧЕ́НИЙ, а, е, прикм. Пом’якшений або '
                                                                         'подрібнений унаслідок товчіння. Приносили '
                                                                         '[баби] на продаж і масличко, і сметану, і '
                                                                         'яєчок, і буханців, і солі товченої '
                                                                         '(Кв.-Осн., II, 1956, 470); Мати поставила на '
                                                                         'стіл ринку з товченою картоплею і миску '
                                                                         'сметани (Тют., Вир, 1964, 8).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}],
    'тікання': [   {   'headword': 'ті́кання',
                       'short_label': 'звуконаслідування монотонних ритмічних звуків годинника',
                       'gloss': 'ticking, rhythmic sound of a clock or timer mechanism',
                       'pos': 'noun',
                       'cefr': 'B1',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[ˈtʲikɐnʲːɑ]'},
                       'stress': {'form': 'ті́кання', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тікання'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'середній',
                                                         'cases': {   'називний': {'singular': 'ті́кання'},
                                                                      'родовий': {'singular': 'ті́кання'},
                                                                      'давальний': {'singular': 'ті́канню'},
                                                                      'знахідний': {'singular': 'ті́кання'},
                                                                      'орудний': {'singular': 'ті́канням'},
                                                                      'місцевий': {'singular': 'ті́канні / ті́канню'},
                                                                      'кличний': {'singular': 'ті́кання'}}}},
                       'distinction_note': 'Означає акустичні звуки ходу годинникового механізму (тікання стрілок, '
                                           'секунд). Не плутати з утечею «тіка́ння».',
                       'meaning': {   'definitions': ['Звуконаслідувальне позначення цокання, тікання годинника.'],
                                      'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'ТІ́КАННЯ, я, с., розм. Дія за знач. ті́кати. '
                                                                        'В кімнаті ставало тихо й тихіше, лиш хлипання '
                                                                        'дощу й.. тікання великого стінного годинника '
                                                                        'переривали тишину (Коб., ІІІ, 1956, 193).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None},
                   {   'headword': 'тіка́ння',
                       'short_label': 'дія з рятування втечею, швидке віддалення або відступ (бігство)',
                       'gloss': 'fleeing, running away, escape, retreat (action)',
                       'pos': 'noun',
                       'cefr': 'B1',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[tʲiˈkɑnʲːɑ]'},
                       'stress': {'form': 'тіка́ння', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тікання'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'середній',
                                                         'cases': {   'називний': {'singular': 'тіка́ння'},
                                                                      'родовий': {'singular': 'тіка́ння'},
                                                                      'давальний': {'singular': 'тіка́нню'},
                                                                      'знахідний': {'singular': 'тіка́ння'},
                                                                      'орудний': {'singular': 'тіка́нням'},
                                                                      'місцевий': {'singular': 'тіка́нні / тіка́нню'},
                                                                      'кличний': {'singular': 'тіка́ння'}}}},
                       'distinction_note': 'Означає втечу, поспішне залишення небезпечного місця (тікання від ворога). '
                                           'Не плутати зі звуком годинника «ті́кання».',
                       'meaning': {'definitions': ['Дія за значенням тікати; втеча.'], 'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'ТІКА́ННЯ, я, с. Дія за знач. тіка́ти 1-6. '
                                                                        'Обернувшись назад і глянувши на небо, вона '
                                                                        'побачила червоні, як грань, хмари — і зразу '
                                                                        'стали зрозумілими їй і той дим, що вона чула, '
                                                                        'і тепло, і неспокій птахів, і тікання звірів '
                                                                        '(Коцюб., І, 1955, 364); Против того дня, що '
                                                                        'їм саме тікать, піп розговорився з попадею '
                                                                        'про тікання (Україна.., І, 1960, 154); Радить '
                                                                        '[Сіхей] покинути край і тікання своє '
                                                                        'приспішити (Зеров, Вибр., 1966, 231).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                 'quote': 'Тікання, -ня, с. Бегство, убеганіе.',
                                                 'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                    'Борисом Грінченком в умовах дії антиукраїнських '
                                                                    'імперських указів (Валуєвського циркуляра 1863 р. '
                                                                    'та Емського указу 1876 р.).'}}],
    'тіпання': [   {   'headword': 'ті́пання',
                       'short_label': "мимовільне нервове здригання м'язів або тремтіння від холоду",
                       'gloss': 'twitching, trembling, nervous spasm, shivering (body)',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[ˈtʲipɐnʲːɑ]'},
                       'stress': {'form': 'ті́пання', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тіпання'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'середній',
                                                         'cases': {   'називний': {   'singular': 'ті́пання',
                                                                                      'plural': 'ті́пання'},
                                                                      'родовий': {   'singular': 'ті́пання',
                                                                                     'plural': 'ті́пань'},
                                                                      'давальний': {   'singular': 'ті́панню',
                                                                                       'plural': 'ті́панням'},
                                                                      'знахідний': {   'singular': 'ті́пання',
                                                                                       'plural': 'ті́пання'},
                                                                      'орудний': {   'singular': 'ті́панням',
                                                                                     'plural': 'ті́паннями'},
                                                                      'місцевий': {   'singular': 'ті́панні',
                                                                                      'plural': 'ті́паннях'},
                                                                      'кличний': {   'singular': 'ті́пання',
                                                                                     'plural': 'ті́пання'}}}},
                       'distinction_note': 'Фізіологічний стан: нервове сіпання повіки чи кінцівки, озноб. Не плутати '
                                           'з первинною обробкою волокон льону «тіпа́ння».',
                       'meaning': {   'definitions': ['Тремтіння, здригання, конвульсивне посмикування.'],
                                      'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'ТІ́ПАННЯ, я, с. Дія за знач. ті́пати і '
                                                                        'ті́патися.',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                 'quote': 'Тіпання, -ня, с. 1) Трясеніе, дрожаніе. 2) С измененным '
                                                          'удареніем: тіпання. Отделеніе кострики от конопли или льва, '
                                                          'трепаніе. Шейк. Ум. тіпаннячко.',
                                                 'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                    'Борисом Грінченком в умовах дії антиукраїнських '
                                                                    'імперських указів (Валуєвського циркуляра 1863 р. '
                                                                    'та Емського указу 1876 р.).'}},
                   {   'headword': 'тіпа́ння',
                       'short_label': 'очищення волокна льону або конопель від костриці тіпалкою',
                       'gloss': 'scutching flax/hemp, beating out wooden core of fibres (craft)',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': {   'classification': 'standard',
                                              'is_russianism': False,
                                              'russian_shadow': False,
                                              'vesum_attested': True},
                       'pronunciation': {'ipa': '[tʲiˈpɑnʲːɑ]'},
                       'stress': {'form': 'тіпа́ння', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тіпання'},
                       'morphology': {   'pos': 'іменник',
                                         'paradigm': {   'kind': 'noun',
                                                         'gender': 'середній',
                                                         'cases': {   'називний': {   'singular': 'тіпа́ння',
                                                                                      'plural': 'тіпа́ння'},
                                                                      'родовий': {   'singular': 'тіпа́ння',
                                                                                     'plural': 'тіпа́нь'},
                                                                      'давальний': {   'singular': 'тіпа́нню',
                                                                                       'plural': 'тіпа́нням'},
                                                                      'знахідний': {   'singular': 'тіпа́ння',
                                                                                       'plural': 'тіпа́ння'},
                                                                      'орудний': {   'singular': 'тіпа́нням',
                                                                                     'plural': 'тіпа́ннями'},
                                                                      'місцевий': {   'singular': 'тіпа́нні',
                                                                                      'plural': 'тіпа́ннях'},
                                                                      'кличний': {   'singular': 'тіпа́ння',
                                                                                     'plural': 'тіпа́ння'}}}},
                       'distinction_note': 'Традиційне сільськогосподарське ремесло: вибивання костриці з льону чи '
                                           "конопель дерев'яною тіпалкою. Не плутати зі спазмом тіла «ті́пання».",
                       'meaning': {   'definitions': [   'Очищення волокна льону чи конопель від костриці за допомогою '
                                                         'тіпалки.'],
                                      'source': 'ВТС'},
                       'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                          'definition': 'ТІПА́ННЯ, я, с. Дія за знач. тіпа́ти. Її '
                                                                        '[корову] купили восени на все, що зібрав '
                                                                        'батько в полі, заробила мати на мочінні та '
                                                                        'тіпанні конопель (Рудь, Гомін.., 1959, 15); У '
                                                                        'добре вилежаного льону під час м’яття і '
                                                                        'тіпання деревина (костриця) вільно і повністю '
                                                                        'відділяється від волокна (Техн. культ., 1956, '
                                                                        '84).',
                                                          'sovietization_risk': 0,
                                                          'keywords': [],
                                                          'historical_note': 'Зафіксовано в радянський період '
                                                                             '(СУМ-11). Наведено для лексикографічної '
                                                                             'прозорості.'},
                       'pre_soviet_witness': None}],
    'тіпати': [   {   'headword': 'ті́пати',
                      'short_label': 'трясти, морозити, смикати від холоду, лихоманки або страху (недок.)',
                      'gloss': 'shake, tremble, shiver with fever or fear; twitch (imperf.)',
                      'pos': 'verb',
                      'cefr': 'B1',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[ˈtʲipɐtɪ]'},
                      'stress': {'form': 'ті́пати', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тіпати'},
                      'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                      'distinction_note': 'Означає трясти, лихоманити людину (його тіпає від холоду). Не плутати з '
                                          'технічною обробкою льону «тіпа́ти».',
                      'meaning': {'definitions': ['Трясти, смикати; бити лихоманкою.'], 'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'ТІ́ПАТИ, аю, аєш, недок. 1. перех. і неперех., '
                                                                       'ким, чим. Короткими ривками, поштовхами хитати '
                                                                       'з боку на бік або зверху вниз; трясти, '
                                                                       'стрясати. В колисці прокинулась дитина. '
                                                                       'Незабаром у хаті було повно плачу. Плакав '
                                                                       'Петько, тіпаючи колиску, плакала дитина (Вас., '
                                                                       '1, 1959, 217); Як узяли ми його [непритомного] '
                                                                       'під пахву, як стали по снігові гасати, як '
                                                                       'почали його тіпати, таскать то взад, то вперед '
                                                                       '(Хотк., I, 1966, 168); // Хитати, махати, '
                                                                       'часто рухати чим-небудь. Знову всі заколесили '
                                                                       'біля столу; поміж другими й старий дяк тіпає '
                                                                       'головою (Мирний, III, 1954, 85); // Ухопивши '
                                                                       'кого-небудь за плечі, руки і т. ін., з силою '
                                                                       'штовхати, смикати, трясти. Але Замфір не '
                                                                       'слухав його: він тільки тіпав бідним циганом '
                                                                       'та кричав йому просто в обличчя (Коцюб., І, '
                                                                       '1955, 212); Доньку мав дуже строгу. Як візьме, '
                                                                       'кажуть, за бороду — у Явтуха борода довжелезна '
                                                                       '— та як почне ним тіпати! (Ю. Янов., II, 1954, '
                                                                       '202); // Викликати здригання, стрясання '
                                                                       'чого-небудь (про плач, судорогу, кашель і т. '
                                                                       'ін.). Нестримне ридання тіпає її тіло (Коз., '
                                                                       'Сальвія, 1959, 111); Її холодні очі зовсім '
                                                                       'скрижаніли, а тонкими устами тіпає нервова '
                                                                       'судорога (Стельмах, І, 1962, 620); Кашель '
                                                                       'тіпав Микитою довго, струшуючи тілом і '
                                                                       'роздимаючи груди (Коз., Гарячі руки, 1960, '
                                                                       '29); // Розвівати, тріпати, шарпати (про вітер '
                                                                       'і т. ін.). Розлютований вітер нещадно тіпав '
                                                                       'буйні, роками не миті махновські чуби (Гончар, '
                                                                       'II, 1959, 430); // безос. — А гу, гу-у!.. '
                                                                       'Страшним голосом перегукувалось щось у степу.. '
                                                                       'А коло вікон щось жалібно вило, просило, '
                                                                       'тужило. На напільному вікні одірвало од степу '
                                                                       'край матки й тіпало нею, як щось живе рукою '
                                                                       '(Вас., І, 1959, 305). ◊ Ми́шка ті́пає '
                                                                       '(ті́пала) що, діал. — судорога зводить '
                                                                       '(зводила) що-небудь. Чіпка пильно дивився на '
                                                                       'діда — очей не спускав… Лице аж пополотніло;.. '
                                                                       'верхню губу мишка тіпала (Мирний, II, 1954, '
                                                                       '62). 2. перех. і ким. Викликати сильне '
                                                                       'тремтіння, дрижання, озноб (про хворобу, '
                                                                       'сильне нервове збудження). Уляні так страшно, '
                                                                       'так страшно, й сама не знає чого; якась трясця '
                                                                       'тіпа її, цокотить зубами, волосся лізе вгору '
                                                                       '(Мирний, І, 1954, 309); Настунею тіпала '
                                                                       'пропасниця, її то жаром обсипало, то проймало '
                                                                       'холодом (Збан., Сеспель, 1961, 343); Плечі '
                                                                       'Нестора тіпала лихоманка, обсипаючи їх '
                                                                       'впереміжку то колючою крупою віхоли, то '
                                                                       'вогнистими снопами іскор (Вол., Озеро.., 1959, '
                                                                       '88); // безос. Про відчуття ким-небудь '
                                                                       'сильного дрожу. Мене тіпало, як у лихоманці. '
                                                                       'Чи правильно зробив? Чи треба було так робити? '
                                                                       'Вирішив — треба (Збан., Малин. дзвін, 1958, '
                                                                       '216); // Ослабляти, знесилювати, мучити '
                                                                       'частими нападами ознобу (про хворобу). Ось уже '
                                                                       'близько двох місяців тіпає його ця виснажлива '
                                                                       'неподатлива хвороба (Добр., Очак. розмир, '
                                                                       '1965, 388); // Викликати сильне нервове '
                                                                       'збудження аж до тремтіння, дрожу (про почуття, '
                                                                       'переживання). В одній хаті жили два вороги,.. '
                                                                       'доволі було якоїсь дрібнички — і злість тіпала '
                                                                       'обома, немов пропасниця (Коцюб., II, 1955, '
                                                                       '21); Віталій Стратонович, ледве перемагаючи '
                                                                       'гнів, бере з рук панотця пропахлу церквою і '
                                                                       'потом камилавку і не знає куди її подіти — так '
                                                                       'обурення тіпає чоловіком (Стельмах, І, 1962, '
                                                                       '334); «Відзначся хоч тут! Відзначся, бо такої '
                                                                       'нагоди не скоро дочекаєшся» — підстрибувала '
                                                                       'совість Федора Свербика, аж тіпала ним (М. Ю. '
                                                                       'Тарн., Незр. горизонт, 1962, 105); // безос. '
                                                                       'Взагалі викликати здригання тіла. Захеканий, '
                                                                       'уткнувся [Іван] дідові в коліна й не міг '
                                                                       'передихнути. — Та вгамуйся, — казав йому дід, '
                                                                       '— хай не тіпає тобою (Гуп., Скупана.., 1965, '
                                                                       '68). 3. Те саме, що ті́патися 2. Тіпають '
                                                                       'плечі.',
                                                         'sovietization_risk': 0,
                                                         'keywords': [],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної '
                                                                            'прозорості.'},
                      'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                'quote': 'Тіпати, -паю, -єш, гл. 1) Дергать, трясти. Тіпати за бороду. '
                                                         'ХС. IV. 23. 2) С измен. удареніем: тіпати. Трепать коноплю, '
                                                         'лен. Рудч. Ск. І. 161. Чуб. VII. 409. Вас. 200. 3) О '
                                                         'лихорадке: трясти. Щодня двома й трома нападами тіпає його '
                                                         'пропасниця. Харьк. г. 4) Колотить, бить. Чи добре таки, чи '
                                                         "погано мене тіпали, кажу ж, не пам'ятаю; знаю тільки, що я "
                                                         'прокинувся в погребі, налигачем скручений. Грин. II. 178.',
                                                'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                   'Борисом Грінченком в умовах дії антиукраїнських '
                                                                   'імперських указів (Валуєвського циркуляра 1863 р. '
                                                                   'та Емського указу 1876 р.).'}},
                  {   'headword': 'тіпа́ти',
                      'short_label': 'очищати стебла льону чи конопель від костриці тіпалкою (недок.)',
                      'gloss': 'scutch, dress flax or hemp by beating with a scutching blade (imperf.)',
                      'pos': 'verb',
                      'cefr': 'B1',
                      'heritage_status': {   'classification': 'standard',
                                             'is_russianism': False,
                                             'russian_shadow': False,
                                             'vesum_attested': True},
                      'pronunciation': {'ipa': '[tʲiˈpɑtɪ]'},
                      'stress': {'form': 'тіпа́ти', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тіпати'},
                      'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                      'distinction_note': 'Сільськогосподарська дія: бити коноплі чи льон знаряддям-тіпалкою для '
                                          'відокремлення волокон. Не плутати з ознобом людини «ті́пати».',
                      'meaning': {   'definitions': [   'Очищати волокна льону, конопель від костриці за допомогою '
                                                        'тіпалки.'],
                                     'source': 'ВТС'},
                      'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                         'definition': 'ТІПА́ТИ, а́ю, а́єш, недок., перех. і без '
                                                                       'додатка. 1. Очищати волокно конопель, льону і '
                                                                       'т. ін. від костриці, вибиваючи на терниці та '
                                                                       'витріпуючи. Я все повимінювала: то за пшоно '
                                                                       'труджене, то відпряду, то поможу конопель '
                                                                       'тіпати (Барв., Опов.., 1902, 484); Зінька '
                                                                       'глянула скоса на Ониську й почервоніла. '
                                                                       'Нагнулась до терниці і тіпала старанно '
                                                                       '(Головко, II, 1957, 25). 2. перен., розм. Бити '
                                                                       'кого-небудь, бити по чомусь; лупцювати. '
                                                                       'Зрештою Андрій не витримав: підбіг до дітей, '
                                                                       'вихопив у одного гарбузячу дудку й почав їх '
                                                                       'тіпати нею по плечах (Вас., II, 1959, 241); — '
                                                                       'А Мартина торік не тіпав на леваді той '
                                                                       'паршивий Комлик? Спасибі, люди розборонили, а '
                                                                       'то на місці поклав би… (Кос., Новели, 1962, '
                                                                       '108).',
                                                         'sovietization_risk': 0,
                                                         'keywords': [],
                                                         'historical_note': 'Зафіксовано в радянський період (СУМ-11). '
                                                                            'Наведено для лексикографічної '
                                                                            'прозорості.'},
                      'pre_soviet_witness': None}],
    'тіпатися': [   {   'headword': 'ті́патися',
                        'short_label': 'дрижати, битися в конвульсіях або здригатися від ознобу чи страху (недок.)',
                        'gloss': 'tremble, shudder, shake uncontrollably (with cold/fear; imperf.)',
                        'pos': 'verb',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[ˈtʲipɐtɪsʲɐ]'},
                        'stress': {'form': 'ті́патися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тіпатися'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                        'distinction_note': 'Означає тремтіти всім тілом, битися від переляку чи холоду («тіпається, '
                                            'як пес у дощ»). Не плутати з пасивним тіпанням льону «тіпа́тися».',
                        'meaning': {   'definitions': [   'Тремтіти, здригатися всім тілом від холоду, хвилювання або '
                                                          'страху.'],
                                       'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ТІ́ПАТИСЯ, аюся, аєшся, недок. 1. Хитатися, '
                                                                         'колихатися. У неї тіло тремтіло й самовар у '
                                                                         'руках тіпався (Мирний, III, 1954, 76); Річко '
                                                                         'моя, зоре ясная!.. Давно вже тіпається, і '
                                                                         'тремтить, і грає тичка моїх ятерів, '
                                                                         'поставлених біля очерету (Чаб., Тече вода.., '
                                                                         '1961, 8); // Розвіватися, метлятися. Спішить '
                                                                         '[Юлча] по пасовиську, Аж під серце коле, Й '
                                                                         'на спідниці-складаниці Тіпаються поли '
                                                                         '(Гойда, Угор. мелодії, 1955, 56). 2. '
                                                                         'Тремтіти, дрижати всім тілом; бути охопленим '
                                                                         'тремтінням, дрожем (про тіло та його '
                                                                         'частини) від холоду, хвороби і т. ін. '
                                                                         'Гафійка мовчала і тіпалась, як у пропасниці. '
                                                                         'Маланка завела її до хати і кинулась світити '
                                                                         'світло (Коцюб., II, 1955, 26); Невгамовний '
                                                                         'хворий тіпався (Кач., II, 1958, 326); — А '
                                                                         'вони [коти] не кусаються? — поцікавився '
                                                                         'Сашко, обережно поглядаючи на рудого кота, '
                                                                         'що вже перестав тіпатися (Чаб., Катюша, '
                                                                         '1960, 52); Тільки тут Шура відчула, що вона '
                                                                         'перемерзла до кісток — все тіло на ній '
                                                                         'тіпалося (Гончар, III, 1959, 190); Руки '
                                                                         'батька.. у п’ятдесят його літ тіпалися, мов '
                                                                         'прив’ялі лопухи на вітрі… (Вол., Озеро.., '
                                                                         '1959, 69); *Образно. Стояли [танки] кілька '
                                                                         'хвилин на пагорбі, захлинаючись спалахами, '
                                                                         'тіпаючись усіма своїми сталевими мускулами '
                                                                         '(Гончар, III, 1959, 370); // Здригатися від '
                                                                         'сильного нервового збудження, викликаного '
                                                                         'певним почуттям (страху, гніву, досади, '
                                                                         'радості і т. ін.). — Хто там? ..«Господи! '
                                                                         'Розбишаки це», — подумала Пріська, вся '
                                                                         'тіпаючись (Мирний, III, 1954, 123); Тепер '
                                                                         'тіло Успенського тіпалось од хвилювання, але '
                                                                         'хвилювання солодкого, як трунок. Тільки з '
                                                                         'чемності він не вистрибнув наперед і не '
                                                                         'крикнув: — Я ж репетитор небожа вашого, Вані '
                                                                         '(Панч, II, 1956, 445); Роксана зблідла і вся '
                                                                         'тіпалася від образи (Хижняк, Д. Галицький, '
                                                                         '1958, 89); Мавра не приховувала свого '
                                                                         'вдоволення: Саливониха аж тіпалася, аж '
                                                                         'пінилася з досади (Горд., Дівчина.., 1954, '
                                                                         '282); // Судорожно сіпатися, смикатися. Сам '
                                                                         '[Віктор] мовчав, а губи і щоки все ще '
                                                                         'пересмикувались, тіпались, ніби продовжували '
                                                                         'говорити (Ряб., Жайворонки, 1957, 128); '
                                                                         'Василь помітив, як злегка тіпалася права '
                                                                         'брова Риндіна (Вл., Аргон. Всесв., 1947, '
                                                                         '76). 3. Сильно, прискорено битися (про '
                                                                         'серце). Серце, — як не вискочить, — '
                                                                         'тіпається, шпарко ганяє гарячу кров по жилах '
                                                                         '(Мирний, І, 1954, 359); Куди ж їй було '
                                                                         'співати, коли сльози душили в горлі, а '
                                                                         'серденько тіпалося від тяжкої образи та '
                                                                         'несправедливості (Збан., Сеспель, 1961, '
                                                                         '369). 4. перен., розм. Відчувати страх, '
                                                                         'боязнь; трепетати. Він любив, щоб усі перед '
                                                                         'ним тіпалися-мліли, падали ниць-хилилися '
                                                                         '(Мирний, III, 1954, 186). 5. розм. Їхати на '
                                                                         'чому-небудь труському; трястися. — Вам, '
                                                                         'певне, обридло тіпатися на поштовій '
                                                                         'тарадайці (Коцюб., І, 1955, 254).',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': {   'witness': 'Грінченко (1907–1909)',
                                                  'quote': 'Тіпатися, -паюся, -єшся, гл. 1) Дрожать, трястись, '
                                                           'судорожно подергиваться; о сердце: сильно биться. '
                                                           'Розмордувавсь, роспаливсь, аж губи тіпаються. Харьк. у. '
                                                           'Тіпається индик після того, як голова одрубана. Мир. ХРВ. '
                                                           '91. Тіпалось серце в Мирона. Мир. ХРВ. 93. 2) С измен. '
                                                           'удареніем: тіпатися. О конопле, льне: трепаться для '
                                                           'очищенія от кострики.',
                                                  'historical_note': 'Автентичне народне мововживання, зафіксоване '
                                                                     'Борисом Грінченком в умовах дії антиукраїнських '
                                                                     'імперських указів (Валуєвського циркуляра 1863 '
                                                                     'р. та Емського указу 1876 р.).'}},
                    {   'headword': 'тіпа́тися',
                        'short_label': 'піддаватися очищенню тіпанням (про льон, коноплі) або розтріпуватися (недок.)',
                        'gloss': 'be scutched (of flax/hemp); fray, tease out (imperf.)',
                        'pos': 'verb',
                        'cefr': 'B1',
                        'heritage_status': {   'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                        'pronunciation': {'ipa': '[tʲiˈpɑtɪsʲɐ]'},
                        'stress': {'form': 'тіпа́тися', 'source': 'ВТС', 'url': 'https://slovnyk.me/dict/vts/тіпатися'},
                        'morphology': {'pos': 'дієслово', 'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                        'distinction_note': 'Пасивний або безособовий стан процесу тіпання волокон. Не плутати з '
                                            'людським здриганням від холоду «ті́патися».',
                        'meaning': {'definitions': ['Піддаватися тіпанню (про льон або коноплі).'], 'source': 'ВТС'},
                        'soviet_colonization_context': {   'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'ТІПА́ТИСЯ, а́ється, недок. Пас. до тіпа́ти. '
                                                                         'Коноплі, льон тіпаються для очищення від '
                                                                         'костриці.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Зафіксовано в радянський період '
                                                                              '(СУМ-11). Наведено для лексикографічної '
                                                                              'прозорості.'},
                        'pre_soviet_witness': None}]}
