"""Curated heteronym dataset (Batch 8) for Word Atlas (#8039, #4387).

This module defines 32 curated heteronym lemmas (64 distinct variants)
expanding the curated heteronym SSOT from 232 to 264 lemmas.

Decolonization & Lexicographical Invariants:
1. Modern standard baseline: Academic СУМ-20 / ВТС / ULIF authorities.
2. Authentic pre-Soviet witness: Грінченко (1907–1909), compiled/published
   under Tsarist Russian imperial bans (Valuev Circular 1863, Ems Ukaz 1876).
3. Soviet colonization context: СУМ-11 (1970–1980) documented transparently
   under `soviet_colonization_context` with `sovietization_risk` and historical notes
   without erasing lexical history.
4. Clean morphology and phonology: Every variant is morphologically verified against VESUM where present, with explicit `vesum_attested: false` where academic dictionaries (ВТС / СУМ-20 / Грінченко) attest substantivized nouns or dialectal variants not registered in VESUM's core lemma list.
"""

from typing import Any

CURATED_HETERONYMS_BATCH_8: dict[str, list[dict[str, Any]]] = { 'вивозитися': [ { 'headword': 'ви́возитися',
                    'short_label': 'забруднитися, замаститися під час роботи (розм., док.)',
                    'gloss': 'get dirty, soil oneself while working or pottering about '
                             '(colloquial, perf.)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[ˈwɪwɔzɪtɪsʲɐ]'},
                    'stress': { 'form': 'ви́возитися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/вивозитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Означає «забруднитися, замаститися, пораючись або '
                                        'працюючи» (розм., доконаний вид). Не плутати з '
                                        '«виво́зитися» (недоконаний вид: пас. до вивозити, '
                                        'експортуватися або виїжджати).',
                    'meaning': { 'definitions': ['Забруднитися, працюючи, пораючись і т. ін.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВИ́ВОЗИТИСЯ, ожуся, озишся, '
                                                                   'док., розм. Забруднитися, '
                                                                   'працюючи, пораючись і т. ін.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}},
                  { 'headword': 'виво́зитися',
                    'short_label': 'транспортуватися звідкись, експортуватися (недок., пас.)',
                    'gloss': 'be exported, transported, removed from somewhere (imperfective '
                             'passive)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[wɪˈwɔzɪtɪsʲɐ]'},
                    'stress': { 'form': 'виво́зитися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/вивозитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Означає «транспортуватися або експортуватися звідкись» '
                                        '(пасивний стан до вивозити; недоконаний вид). Не плутати '
                                        'з доконаним розмовним «ви́возитися» (забруднитися).',
                    'meaning': { 'definitions': [ 'Пасивний стан до виво́зити: транспортуватися, '
                                                  'переміщатися звідкись транспортними засобами.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВИВО́ЗИТИСЯ, иється, недок. '
                                                                   'Пас. до виво́зити.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}}],
  'виганятися': [ { 'headword': 'ви́ганятися',
                    'short_label': 'втомитися від тривалого бігу (розм., док.)',
                    'gloss': 'tire oneself out by running around a lot, exhaust oneself from '
                             'running (colloquial, perf.)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'authentic-dialectism',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[ˈwɪɦɐnʲɐtɪsʲɐ]'},
                    'stress': { 'form': 'ви́ганятися',
                                'source': 'Грінченко (1907) / ВТС',
                                'url': 'https://slovnyk.me/dict/vts/виганятися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Означає «багато бігаючи, втомитися» (Сл. Грінченка: '
                                        '«Виганявся за день, аж ніг не чую»; доконаний вид). Не '
                                        'плутати з пасивним «виганя́тися» (бути вигнаним).',
                    'meaning': { 'definitions': [ 'Багато бігаючи, втомитися, знесилитися від '
                                                  'швидкого руху.'],
                                 'source': 'Грінченко (1907) / ВТС'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВИ́ГАНЯТИСЯ, яюся, яєшся, док. '
                                                                   'Багато бігаючи, втомитися. '
                                                                   'Виганявся за день, аж ніг не '
                                                                   'чую (Сл. Гр.).',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в Словнику '
                                                                        'Бориса Грінченка '
                                                                        '(1907–1909), укладеному '
                                                                        'всупереч антиукраїнським '
                                                                        'імперським заборонам '
                                                                        '(Валуєвський циркуляр '
                                                                        '1863 р., Емський указ '
                                                                        '1876 р.).'}},
                  { 'headword': 'виганя́тися',
                    'short_label': 'бути вигнаним, виганятися геть або на пашу (недок., пас.)',
                    'gloss': 'be expelled, driven out, chased away, or driven to pasture '
                             '(imperfective passive)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[wɪɦɐˈnʲɑtɪsʲɐ]'},
                    'stress': { 'form': 'виганя́тися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/виганятися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Означає «бути виганяним (на пашу, з приміщення тощо)» '
                                        '(пасивний стан до виганяти; недоконаний вид). Не плутати '
                                        'з доконаним «ви́ганятися» (втомитися від бігу).',
                    'meaning': { 'definitions': [ 'Пасивний стан до виганя́ти: бути виселюваним, '
                                                  'проганяним або виганяним на випас.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВИГАНЯ́ТИСЯ, я́юся, я́єшся, '
                                                                   'недок. 1. Пас. до виганя́ти. '
                                                                   '2. тільки 3 ос. Виростати, '
                                                                   'підростати у висоту, '
                                                                   'видовжуватися.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}}],
  'вигасати': [ { 'headword': 'ви́гасати',
                  'short_label': 'побувати скрізь, гасаючи (розм., док.)',
                  'gloss': 'dash/rush all over many places, visit everywhere by darting around '
                           '(colloquial, perf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[ˈwɪɦɐsɐtɪ]'},
                  'stress': { 'form': 'ви́гасати',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/вигасати'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає «гасаючи, побувати в багатьох місцях або скрізь» '
                                      '(розм., доконаний вид). Не плутати з «вигаса́ти» '
                                      '(недоконаний вид: поступово гаснути, згасати).',
                  'meaning': { 'definitions': ['Гасаючи, побувати в багатьох місцях або скрізь.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ВИ́ГАСАТИ, аю, аєш, док., розм. '
                                                                 'Гасаючи, побувати в багатьох '
                                                                 'місцях або скрізь.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський '
                                                                      'період (СУМ-11). Наведено '
                                                                      'для лексикографічної '
                                                                      'прозорості.'}},
                { 'headword': 'вигаса́ти',
                  'short_label': 'переставати горіти, згасати, тьмяніти (недок.)',
                  'gloss': 'fade out, die down, extinguish gradually, cease burning (imperfective)',
                  'pos': 'verb',
                  'cefr': 'B1',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[wɪɦɐˈsɑtɪ]'},
                  'stress': { 'form': 'вигаса́ти',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/вигасати'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Означає «переставати горіти, світитися; згасати, втрачати '
                                      'яскравість» (недоконаний вид). Не плутати з доконаним '
                                      'розмовним «ви́гасати» (побувати скрізь, гасаючи).',
                  'meaning': { 'definitions': [ 'Переставати світитися або горіти; затухати, '
                                                'тьмяніти, згасати.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ВИГАСА́ТИ, а́є, недок., '
                                                                 'ВИ́ГАСНУТИ, не; док. Переставати '
                                                                 'світитися, світити або горіти; '
                                                                 'гаснути.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський '
                                                                      'період (СУМ-11). Наведено '
                                                                      'для лексикографічної '
                                                                      'прозорості.'}}],
  'виповзати': [ { 'headword': 'ви́повзати',
                   'short_label': 'облазити повзком або випросити поповзом (док.)',
                   'gloss': 'crawl all over something, explore by crawling; obtain by groveling '
                            '(perfective)',
                   'pos': 'verb',
                   'cefr': 'B2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[ˈwɪpɔwzɐtɪ]'},
                   'stress': { 'form': 'ви́повзати',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/виповзати'},
                   'morphology': { 'pos': 'дієслово',
                                   'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                   'distinction_note': 'Означає «повзаючи, облазити щось» або переносно '
                                       '«випросити, плазуючи перед кимось» (доконаний вид). Не '
                                       'плутати з «виповза́ти» (недоконаний вид: рухатися повзком '
                                       'зсередини назовні).',
                   'meaning': { 'definitions': [ 'Повзаючи, облазити що-небудь; домагатися чогось '
                                                 'плазуванням перед кимось.'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ВИ́ПОВЗАТИ, аю, аєш, док., '
                                                                  'перех. 1. Повзаючи, облазити '
                                                                  'що-небудь. 2. Домогтися '
                                                                  'чого-небудь, повзаючи перед '
                                                                  'кимсь.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський '
                                                                       'період (СУМ-11). Наведено '
                                                                       'для лексикографічної '
                                                                       'прозорості.'}},
                 { 'headword': 'виповза́ти',
                   'short_label': 'повзти зсередини назовні, вилазити повзком (недок.)',
                   'gloss': 'crawl out, creep forth, emerge crawling from inside to outside '
                            '(imperfective)',
                   'pos': 'verb',
                   'cefr': 'B1',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[wɪpɔwˈzɑtɪ]'},
                   'stress': { 'form': 'виповза́ти',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/виповзати'},
                   'morphology': { 'pos': 'дієслово',
                                   'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                   'distinction_note': 'Означає «рухатися повзком зсередини назовні, висуватися на '
                                       'поверхню» (недоконаний вид). Не плутати з доконаним '
                                       '«ви́повзати» (облазити повзком).',
                   'meaning': { 'definitions': [ 'Повзком вибиратися, переміщатися звідки-небудь '
                                                 'назовні або на поверхню.'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ВИПОВЗА́ТИ, а́ю, а́єш, недок., '
                                                                  'ВИ́ПОВЗТИ, зу, зеш, док. 1. '
                                                                  'Повзком переміщатися '
                                                                  'звідки-небудь, наближатися до '
                                                                  'когось.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський '
                                                                       'період (СУМ-11). Наведено '
                                                                       'для лексикографічної '
                                                                       'прозорості.'}}],
  'виполювати': [ { 'headword': 'ви́полювати',
                    'short_label': 'здобути на полюванні дичину (розм., док.)',
                    'gloss': 'bag, track down, catch while hunting game (colloquial, perf.)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[ˈwɪpɔlʲʊwɐtɪ]'},
                    'stress': { 'form': 'ви́полювати',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/виполювати'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Означає «здобути на полюванні звіра чи птаха» (розм., '
                                        'доконаний вид). Не плутати з аграрним «випо́лювати» '
                                        "(недоконаний вид: прополювати бур'ян).",
                    'meaning': { 'definitions': [ 'Здобути, підстрелити на полюванні (дичину, '
                                                  'звіра).'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВИ́ПОЛЮВАТИ, юю, юєш, док., '
                                                                   'перех., розм. Здобути на '
                                                                   'полюванні (дичину).',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}},
                  { 'headword': 'випо́лювати',
                    'short_label': "виривати бур'яни, полоти ділянку (недок.)",
                    'gloss': 'weed out, remove weeds, hoe up noxious plants from a field '
                             '(imperfective)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[wɪˈpɔlʲʊwɐtɪ]'},
                    'stress': { 'form': 'випо́лювати',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/виполювати'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': "Означає «виривати із землі бур'яни, очищати посіви від "
                                        "бур'яну» (недоконаний вид). Не плутати з мисливським "
                                        '«ви́полювати» (здобути на полюванні).',
                    'meaning': { 'definitions': [ "Полючи, видаляти бур'яни; очищати землю чи "
                                                  'посіви від зайвих рослин.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВИПО́ЛЮВАТИ, юю, юєш, недок., '
                                                                   'ВИ́ПОЛОТИ, лю, леш, док., '
                                                                   'перех. Полючи, видаляти '
                                                                   "(бур'ян); полоти все чи багато "
                                                                   'чого-небудь.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}}],
  'ворочатися': [ { 'headword': 'воро́чатися',
                    'short_label': 'перевертатися з боку на бік (недок., розм.)',
                    'gloss': 'toss and turn, roll from side to side, turn over in bed (colloquial, '
                             'imperf.)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[wɔˈrɔt͡ʃɐtɪsʲɐ]'},
                    'stress': { 'form': 'воро́чатися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/ворочатися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Означає «перевертатися з боку на бік, крутитися в ліжку» '
                                        '(недоконаний вид; те саме, що перевертатися). Не плутати '
                                        'з просторічним «вороча́тися» (повертатися назад).',
                    'meaning': { 'definitions': [ 'Перевертатися з боку на бік; неспокійно лежати, '
                                                  'ворушитися в ліжку.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВОРО́ЧАТИСЯ, аюся, аєшся, '
                                                                   'недок., розм., рідко. Те саме, '
                                                                   'що переверта́тися 1.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}},
                  { 'headword': 'вороча́тися',
                    'short_label': 'повертатися назад, вертатися (недок., розм.)',
                    'gloss': 'turn back, return, come back (colloquial/vernacular, imperf.)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[wɔrɔˈt͡ʃɑtɪsʲɐ]'},
                    'stress': { 'form': 'вороча́тися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/ворочатися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Означає «повертатися назад, вертатися на попереднє місце» '
                                        '(недоконаний вид; розмовний варіант до повертатися). Не '
                                        'плутати з «воро́чатися» (крутитися, перевертатися з боку '
                                        'на бік).',
                    'meaning': { 'definitions': [ 'Повертатися назад, іти або їхати туди, звідки '
                                                  'вийшов; повертатися.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ВОРОЧА́ТИСЯ, а́юся, а́єшся, '
                                                                   'недок., розм., рідко. Те саме, '
                                                                   'що поверта́тися 1, 2.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}}],
  'гикання': [ { 'headword': 'ги́кання',
                 'short_label': 'голосні окрики «гик!», свист і крики поганяння (розм.)',
                 'gloss': "whooping, shouting 'hyk!', hooting and cracking yells at horses "
                          '(colloquial)',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': { 'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                 'pronunciation': {'ipa': '[ˈɦɪkɐnʲːɐ]'},
                 'stress': { 'form': 'ги́кання',
                             'source': 'ВТС / СУМ-11',
                             'url': 'https://slovnyk.me/dict/vts/гикання'},
                 'morphology': { 'pos': 'іменник',
                                 'paradigm': { 'kind': 'noun',
                                               'gender': 'neuter',
                                               'animacy': 'inanimate'}},
                 'distinction_note': 'Означає «вигукування вигуку «гик!», крик погонича або '
                                     'підбадьорливий свист» (дія за знач. ги́кати). Не плутати з '
                                     'фізіологічним «гика́ння» (гикавка).',
                 'meaning': { 'definitions': [ 'Дія за значенням ги́кати: видавання звуків «гик», '
                                               'голосні вигуки або свист.'],
                              'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ГИ́КАННЯ, я, с., розм. Дія за '
                                                                'знач. ги́кати.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський '
                                                                     'період (СУМ-11). Наведено '
                                                                     'для лексикографічної '
                                                                     'прозорості.'}},
               { 'headword': 'гика́ння',
                 'short_label': 'фізіологічна гикавка, спазматичні звуки (розм.)',
                 'gloss': 'hiccuping, spasmatic sounds produced by involuntary contractions of '
                          'diaphragm',
                 'pos': 'noun',
                 'cefr': 'B1',
                 'heritage_status': { 'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                 'pronunciation': {'ipa': '[ɦɪˈkɑnʲːɐ]'},
                 'stress': { 'form': 'гика́ння',
                             'source': 'ВТС / СУМ-11',
                             'url': 'https://slovnyk.me/dict/vts/гикання'},
                 'morphology': { 'pos': 'іменник',
                                 'paradigm': { 'kind': 'noun',
                                               'gender': 'neuter',
                                               'animacy': 'inanimate'}},
                 'distinction_note': 'Означає «мимовільні спазматичні вдихи, гикавка» (дія за '
                                     'знач. гика́ти). Не плутати з окриками погонича «ги́кання».',
                 'meaning': { 'definitions': [ 'Дія за значенням гика́ти: мимовільне судомне '
                                               'скорочення діафрагми, гикавка.'],
                              'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ГИКА́ННЯ, я, с., розм. Дія за '
                                                                'знач. гика́ти.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський '
                                                                     'період (СУМ-11). Наведено '
                                                                     'для лексикографічної '
                                                                     'прозорості.'}}],
  'довозитися': [ { 'headword': 'дово́зитися',
                    'short_label': 'бути доставленим, доправленим транспортом (недок., пас.)',
                    'gloss': 'be delivered, conveyed, transported to destination (imperfective '
                             'passive)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[dɔˈwɔzɪtɪsʲɐ]'},
                    'stress': { 'form': 'дово́зитися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/довозитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Означає «доправлятися, перевозитися до місця призначення» '
                                        '(пасивний стан до довозити; недоконаний вид). Не плутати '
                                        'з доконаним «довози́тися» (зазнати неприємностей від '
                                        'довгого візництва).',
                    'meaning': { 'definitions': [ 'Пасивний стан до дово́зити: доправлятися '
                                                  'транспортом до потрібного пункту чи межі.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ДОВО́ЗИТИСЯ, иться, недок. '
                                                                   'Пас. до дово́зити.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}},
                  { 'headword': 'довози́тися',
                    'short_label': 'довго возячи щось/когось, зазнати клопоту (розм., док.)',
                    'gloss': 'suffer trouble or fatigue from excessive carting/driving '
                             '(colloquial, perf.)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[dɔwɔˈzɪtɪsʲɐ]'},
                    'stress': { 'form': 'довози́тися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/довозитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Означає «возячи кого-, що-небудь, зазнати неприємностей '
                                        'або клопоту» (розм., доконаний вид). Не плутати з '
                                        'пасивним недоконаним «дово́зитися» (доправлятися).',
                    'meaning': { 'definitions': [ 'Возячи кого-, що-небудь, зазнати неприємностей, '
                                                  'ускладнень або втомитися від візництва.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ДОВОЗИ́ТИСЯ, ожу́ся, о́зишся, '
                                                                   'док. 1. Возячи кого-, '
                                                                   'що-небудь, зазнати '
                                                                   'неприємностей.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}}],
  'доходитися': [ { 'headword': 'дохо́дитися',
                    'short_label': 'бути змушеним щось робити, доходити до стану (недок., безос.)',
                    'gloss': 'come to a pass, be compelled/forced to do something (imperfective '
                             'impersonal)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[dɔˈxɔdɪtɪsʲɐ]'},
                    'stress': { 'form': 'дохо́дитися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/доходитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Означає безособово «бути змушеним що-небудь робити, '
                                        'доходити до складного стану» (недоконаний вид; те саме, '
                                        'що дійтися). Не плутати з доконаним особовим '
                                        '«доходи́тися» (втомитися від ходіння).',
                    'meaning': { 'definitions': [ 'Безособово: бути змушеним чимось займатися або '
                                                  'доходити до крайнього становища.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ДОХО́ДИТИСЯ, иться, недок., '
                                                                   'ДІЙТИ́СЯ, ді́йдеться, док., '
                                                                   'безос. 1. Бути змушеним '
                                                                   'що-небудь робити.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}},
                  { 'headword': 'доходи́тися',
                    'short_label': 'довго ходячи, втомитися або догулятися до лиха (розм., док.)',
                    'gloss': 'exhaust oneself by prolonged walking, walk oneself into trouble '
                             '(colloquial, perf.)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[dɔxɔˈdɪtɪsʲɐ]'},
                    'stress': { 'form': 'доходи́тися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/доходитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Означає «довго ходячи, втомитися або дійти до '
                                        'неприємностей» (розм., доконаний вид). Не плутати з '
                                        'безособовим «дохо́дитися» (бути змушеним діяти).',
                    'meaning': { 'definitions': [ 'Довго або багато ходячи, втомитися; догулятися '
                                                  'чи доходитися до неприємностей.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ДОХОДИ́ТИСЯ, ходжу́ся, '
                                                                   'хо́дишся, док. 1. розм. Довго '
                                                                   'ходячи, втомитися. 2. перен., '
                                                                   'фам. Дійшовши до якого-небудь '
                                                                   'стану, зазнати лиха.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}}],
  'дякування': [ { 'headword': 'дя́кування',
                   'short_label': 'висловлення подяки, вдячність (літературна норма)',
                   'gloss': 'expression of thanks, gratitude, act of thanking (standard normative '
                            'accent)',
                   'pos': 'noun',
                   'cefr': 'A2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[ˈdʲɑkʊwɐnʲːɐ]'},
                   'stress': { 'form': 'дя́кування',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/дякування'},
                   'morphology': { 'pos': 'іменник',
                                   'paradigm': { 'kind': 'noun',
                                                 'gender': 'neuter',
                                                 'animacy': 'inanimate'}},
                   'distinction_note': 'Нормативний наголос на корені: дія за значенням дя́кувати '
                                       '(висловлення вдячності). Форма «дякува́ння» є традиційним '
                                       'розмовно-поетичним варіантом.',
                   'meaning': { 'definitions': [ 'Дія за значенням дя́кувати; слова або вияви '
                                                 'вдячності.'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ДЯ́КУВАННЯ і ДЯКУВА́ННЯ, я, с. '
                                                                  'Дія за знач. дя́кувати.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський '
                                                                       'період (СУМ-11). Наведено '
                                                                       'для лексикографічної '
                                                                       'прозорості.'}},
                 { 'headword': 'дякува́ння',
                   'short_label': 'висловлення подяки (традиційний акцентний варіант)',
                   'gloss': 'expression of gratitude (traditional poetic/dialectal suffixal accent '
                            'variant)',
                   'pos': 'noun',
                   'cefr': 'B1',
                   'heritage_status': { 'classification': 'authentic-dialectism',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[dʲɑkʊˈwɑnʲːɐ]'},
                   'stress': { 'form': 'дякува́ння',
                               'source': 'Грінченко (1907) / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/дякування'},
                   'morphology': { 'pos': 'іменник',
                                   'paradigm': { 'kind': 'noun',
                                                 'gender': 'neuter',
                                                 'animacy': 'inanimate'}},
                   'distinction_note': 'Традиційний варіант із суфіксальним наголосом: дія за '
                                       'значенням дякувати. У сучасній літературній нормі '
                                       'переважає кореневий акцент «дя́кування».',
                   'meaning': { 'definitions': [ 'Акцентний варіант до дя́кування: висловлення '
                                                 'подяки чи визнання.'],
                                'source': 'Грінченко (1907) / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ДЯ́КУВАННЯ і ДЯКУВА́ННЯ, я, с. '
                                                                  'Дія за знач. дя́кувати.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в Словнику '
                                                                       'Бориса Грінченка '
                                                                       '(1907–1909) та СУМ-11.'}}],
  'замикатися': [ { 'headword': 'замика́тися',
                    'short_label': 'зачинятися на замок, ізолюватися від світу (недок.)',
                    'gloss': 'lock oneself up, close on a lock, become introverted/isolated '
                             '(imperfective)',
                    'pos': 'verb',
                    'cefr': 'A2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[zɐmɪˈkɑtɪsʲɐ]'},
                    'stress': { 'form': 'замика́тися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/замикатися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Означає «зачинятися на замок» або «ставати '
                                        'відлюдькуватим, зосереджуватися на собі» (недоконаний '
                                        'вид). Не плутати з доконаним розмовним «зами́катися» '
                                        '(втомитися від блукання).',
                    'meaning': { 'definitions': [ 'Зачинятися на замок або засув; зосереджуватися '
                                                  'в собі, усамітнюватися.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ЗАМИКА́ТИСЯ, а́юся, а́єшся, '
                                                                   'недок., ЗАМКНУ́ТИСЯ, ну́ся, '
                                                                   'не́шся, док. 1. Замикати двері '
                                                                   'кімнати, в якій сам '
                                                                   'перебуваєш.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в радянський '
                                                                        'період (СУМ-11). Наведено '
                                                                        'для лексикографічної '
                                                                        'прозорості.'}},
                  { 'headword': 'зами́катися',
                    'short_label': 'втомитися від тривалого блукання (розм., док.)',
                    'gloss': 'exhaust oneself by prolonged wandering/roaming, wear oneself out '
                             'tramping (colloquial, perf.)',
                    'pos': 'verb',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'authentic-dialectism',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[zɐˈmɪkɐtɪsʲɐ]'},
                    'stress': { 'form': 'зами́катися',
                                'source': 'Грінченко (1907) / ВТС',
                                'url': 'https://slovnyk.me/dict/vts/замикатися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Означає «довго блукаючи, микаючись, втомитися» (від '
                                        'дієслова микатися; розм., доконаний вид). Не плутати з '
                                        '«замика́тися» (замикати замок).',
                    'meaning': { 'definitions': [ 'Блукаючи, микаючись по різних місцях, '
                                                  'знесилитися або втомитися.'],
                                 'source': 'Грінченко (1907) / ВТС'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'ЗАМИ́КАТИСЯ, аюся, аєшся, '
                                                                   'док., розм. Микаючись (у 3 '
                                                                   'знач.), втомитися.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зафіксовано в Словнику '
                                                                        'Бориса Грінченка '
                                                                        '(1907–1909) та СУМ-11.'}}],
  'заспоритися': [ { 'headword': 'заспо́ритися',
                     'short_label': 'почати сперечатися, завести суперечку (док.)',
                     'gloss': 'begin arguing, start disputing/quarreling with someone (perfective)',
                     'pos': 'verb',
                     'cefr': 'B1',
                     'heritage_status': { 'classification': 'standard',
                                          'is_russianism': False,
                                          'russian_shadow': False,
                                          'vesum_attested': True},
                     'pronunciation': {'ipa': '[zɐˈspɔrɪtɪsʲɐ]'},
                     'stress': { 'form': 'заспо́ритися',
                                 'source': 'ВТС / СУМ-11',
                                 'url': 'https://slovnyk.me/dict/vts/заспоритися'},
                     'morphology': { 'pos': 'дієслово',
                                     'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                     'distinction_note': "Означає «почати сперечатися, зав'язати палку дискусію» "
                                         '(доконаний вид; від спорити). Не плутати з '
                                         '«заспори́тися» (про роботу: піти успішно, з користю).',
                     'meaning': { 'definitions': [ 'Почати сперечатися з ким-небудь, завести '
                                                   'суперечку.'],
                                  'source': 'ВТС / СУМ-11'},
                     'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                      'definition': 'ЗАСПО́РИТИСЯ, рюся, ришся, '
                                                                    'док. Почати сперечатися, '
                                                                    'завести суперечку.',
                                                      'sovietization_risk': 0,
                                                      'keywords': [],
                                                      'historical_note': 'Зафіксовано в радянський '
                                                                         'період (СУМ-11). '
                                                                         'Наведено для '
                                                                         'лексикографічної '
                                                                         'прозорості.'}},
                   { 'headword': 'заспори́тися',
                     'short_label': 'піти успішно, з користю, почати ладитися (про роботу, док.)',
                     'gloss': 'go smoothly, proceed fruitfully, prosper, start going briskly (of '
                              'work, perf.)',
                     'pos': 'verb',
                     'cefr': 'B2',
                     'heritage_status': { 'classification': 'authentic-dialectism',
                                          'is_russianism': False,
                                          'russian_shadow': False,
                                          'vesum_attested': True},
                     'pronunciation': {'ipa': '[zɐspɔˈrɪtɪsʲɐ]'},
                     'stress': { 'form': 'заспори́тися',
                                 'source': 'Грінченко (1907) / ВТС',
                                 'url': 'https://slovnyk.me/dict/vts/заспоритися'},
                     'morphology': { 'pos': 'дієслово',
                                     'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                     'distinction_note': 'Означає «піти успішно, ладитися, споритися» (про діло, '
                                         'працю: робота заспорилася; доконаний вид). Не плутати зі '
                                         'словесною сваркою «заспо́ритися».',
                     'meaning': { 'definitions': [ 'Піти успішно, з користю, почати ладитися, '
                                                   'добре споритися (про роботу чи справу).'],
                                  'source': 'Грінченко (1907) / ВТС'},
                     'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                      'definition': 'ЗАСПОРИ́ТИСЯ, и́ться, док. '
                                                                    'Піти успішно, з користю.',
                                                      'sovietization_risk': 0,
                                                      'keywords': [],
                                                      'historical_note': 'Зафіксовано в Словнику '
                                                                         'Бориса Грінченка '
                                                                         '(1907–1909) та '
                                                                         'СУМ-11.'}}],
  'захватний': [ { 'headword': 'захва́тний',
                   'short_label': 'загарбницький, спрямований на загарбання (рідко)',
                   'gloss': 'predatory, aggressive, aimed at conquest or seizure (rare)',
                   'pos': 'adjective',
                   'cefr': 'B2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[zɐxˈwɑtnɪj]'},
                   'stress': { 'form': 'захва́тний',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/захватний'},
                   'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                   'distinction_note': 'Означає «який має на меті загарбання, захват чужого» '
                                       '(рідкісний прикметник). Не плутати з технічним терміном '
                                       '«захватни́й» (пристосований для тримання чи підняття '
                                       'вантажів).',
                   'meaning': { 'definitions': [ 'Який має на меті захват, захоплення чого-небудь; '
                                                 'загарбницький.'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ЗАХВА́ТНИЙ, а, е. 1. рідко. '
                                                                  'Який має на меті захват, '
                                                                  'захоплення чого-небудь; '
                                                                  'загарбницький.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський '
                                                                       'період (СУМ-11). Наведено '
                                                                       'для лексикографічної '
                                                                       'прозорості.'}},
                 { 'headword': 'захватни́й',
                   'short_label': 'технічний: призначений для захоплення, тримання деталей',
                   'gloss': 'gripping, clamping, clutching, gripping mechanism/clamp in '
                            'engineering',
                   'pos': 'adjective',
                   'cefr': 'B2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[zɐxwɐtˈnɪj]'},
                   'stress': { 'form': 'захватни́й',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/захватний'},
                   'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                   'distinction_note': 'Технічний термін: «призначений для захоплювання, '
                                       'затискання або підіймання вантажів чи деталей» (захватний '
                                       'пристрій, механізм). Не плутати з «захва́тний» '
                                       '(загарбницький).',
                   'meaning': { 'definitions': [ 'Спеціальний пристрій або деталь, призначена для '
                                                 'затискання, підіймання чи утримування '
                                                 'предметів.'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ЗАХВАТНИ́Й, а́, е́, техн. '
                                                                  'Пристосований, признач. для '
                                                                  'захвату (у 3 знач.). Захватні '
                                                                  'пристрої.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський '
                                                                       'період (СУМ-11). Наведено '
                                                                       'для лексикографічної '
                                                                       'прозорості.'}}],
  'зачадіти': [ { 'headword': 'зача́діти',
                  'short_label': 'отруїтися чадним газом, димом (док.)',
                  'gloss': 'be poisoned/asphyxiated by carbon monoxide or smoke (perfective)',
                  'pos': 'verb',
                  'cefr': 'B1',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[zɐˈt͡ʃɑdʲitɪ]'},
                  'stress': { 'form': 'зача́діти',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/зачадіти'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає «отруїтися димом або чадним газом» (неперехідне '
                                      'дієслово стану, доконаний вид). Не плутати з «зачаді́ти» '
                                      '(почати виділяти чад і дим; закоптити).',
                  'meaning': { 'definitions': [ 'Отруїтися чадом, димом від несправної печі або '
                                                'вогню.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ЗАЧА́ДІТИ, ію, ієш, док. '
                                                                 'Отруїтися чадом, димом.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в радянський '
                                                                      'період (СУМ-11). Наведено '
                                                                      'для лексикографічної '
                                                                      'прозорості.'}},
                { 'headword': 'зачаді́ти',
                  'short_label': 'почати виділяти чад, задимити приміщення (док.)',
                  'gloss': 'start emitting toxic fumes/soot, fill with smoke and fumes '
                           '(perfective)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'authentic-dialectism',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[zɐt͡ʃɐˈdʲitɪ]'},
                  'stress': { 'form': 'зачаді́ти',
                              'source': 'Грінченко (1907) / ВТС',
                              'url': 'https://slovnyk.me/dict/vts/зачадіти'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Означає «почати чадіти, виділяти задушливий дим чи чад» (те '
                                      'саме, що зачадити; доконаний вид). Не плутати з отруєнням '
                                      'людини «зача́діти».',
                  'meaning': { 'definitions': [ 'Почати виділяти чад, наповнити приміщення димом і '
                                                'кіптявою.'],
                               'source': 'Грінченко (1907) / ВТС'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ЗАЧАДІ́ТИ, джу́, ди́ш, док. Те '
                                                                 'саме, що зачади́ти 1.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в Словнику '
                                                                      'Бориса Грінченка '
                                                                      '(1907–1909) та СУМ-11.'}}],
  'значитися': [ { 'headword': 'зна́читися',
                   'short_label': 'бути внесеним до списку, числитися; важити (недок.)',
                   'gloss': 'be registered/listed, be on a roster; signify, have meaning '
                            '(imperfective)',
                   'pos': 'verb',
                   'cefr': 'B1',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[ˈznɑt͡ʃɪtɪsʲɐ]'},
                   'stress': { 'form': 'зна́читися',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/значитися'},
                   'morphology': { 'pos': 'дієслово',
                                   'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                   'distinction_note': 'Означає «бути внесеним до списку, числитися десь» або '
                                       '«мати значення, важити» (недоконаний вид). Не плутати з '
                                       '«значи́тися» (виділятися, помічатися).',
                   'meaning': { 'definitions': [ 'Бути записаним, внесеним до якогось реєстру чи '
                                                 'списку; мати певне значення.'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ЗНА́ЧИТИСЯ, чуся, чишся, недок. '
                                                                  '1. Бути записаним, внесеним до '
                                                                  'якогось списку; числитися '
                                                                  'де-небудь. 2. Мати певне '
                                                                  'значення, важити.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський '
                                                                       'період (СУМ-11). Наведено '
                                                                       'для лексикографічної '
                                                                       'прозорості.'}},
                 { 'headword': 'значи́тися',
                   'short_label': 'виділятися, помічатися, чітко позначатися (рідко, недок.)',
                   'gloss': 'stand out, show through, be noticeably marked or outlined (rare, '
                            'imperf.)',
                   'pos': 'verb',
                   'cefr': 'B2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[znɐˈt͡ʃɪtɪsʲɐ]'},
                   'stress': { 'form': 'значи́тися',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/значитися'},
                   'morphology': { 'pos': 'дієслово',
                                   'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                   'distinction_note': 'Означає «позначатися, вирізнятися на тлі, бути помітним» '
                                       '(рідко, недоконаний вид). Не плутати з «зна́читися» '
                                       '(числитися в списках).',
                   'meaning': { 'definitions': [ 'Виділятися, виразно помічатися або позначатися '
                                                 'на чому-небудь.'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'ЗНАЧИ́ТИСЯ, чи́ться, недок., '
                                                                  'рідко. Виділятися, помічатися; '
                                                                  'позначатися.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Зафіксовано в радянський '
                                                                       'період (СУМ-11). Наведено '
                                                                       'для лексикографічної '
                                                                       'прозорості.'}}],
  'зольник': [ { 'headword': 'зо́льник',
                 'short_label': "археологічна пам'ятка: курганоподібний насип із золою",
                 'gloss': 'ash-mound archaeological site, prehistoric ceremonial or settlement ash '
                          'heap',
                 'pos': 'noun',
                 'cefr': 'C1',
                 'heritage_status': { 'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                 'pronunciation': {'ipa': '[ˈzɔlʲnɪk]'},
                 'stress': { 'form': 'зо́льник',
                             'source': 'ВТС / СУМ-11',
                             'url': 'https://slovnyk.me/dict/vts/зольник'},
                 'morphology': { 'pos': 'іменник',
                                 'paradigm': { 'kind': 'noun',
                                               'gender': 'masculine',
                                               'animacy': 'inanimate'}},
                 'distinction_note': 'Археологічний термін: «курганоподібний насип з попелом, '
                                     'золою та рештками побуту стародавніх городищ». Не плутати з '
                                     'виробничим резервуаром чи піддувалом «зольни́к».',
                 'meaning': { 'definitions': [ 'Особливий тип археологічних пам’яток у вигляді '
                                               'курганоподібних насипів із шарами попелу.'],
                              'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ЗО́ЛЬНИК, а, ч., арх. Особливий '
                                                                'тип археологічних пам’яток у '
                                                                'вигляді курганоподібних насипів.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський '
                                                                     'період (СУМ-11). Наведено '
                                                                     'для лексикографічної '
                                                                     'прозорості.'}},
               { 'headword': 'зольни́к',
                 'short_label': 'чан для вимочування шкіри в золі або піддувало печі',
                 'gloss': 'ash-pit in furnace / tanning vat containing lye or ash for soaking '
                          'hides',
                 'pos': 'noun',
                 'cefr': 'B2',
                 'heritage_status': { 'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                 'pronunciation': {'ipa': '[zɔlʲˈnɪk]'},
                 'stress': { 'form': 'зольни́к',
                             'source': 'ВТС / СУМ-11',
                             'url': 'https://slovnyk.me/dict/vts/зольник'},
                 'morphology': { 'pos': 'іменник',
                                 'paradigm': { 'kind': 'noun',
                                               'gender': 'masculine',
                                               'animacy': 'inanimate'}},
                 'distinction_note': 'Спеціальний термін: «чан, яма з розчином вапна або золи для '
                                     'зоління шкір у кушнірстві» або «піддувало, камера під '
                                     'колосниками для збирання попелу». Не плутати з археологічним '
                                     'курганом «зо́льник».',
                 'meaning': { 'definitions': [ 'Яма чи резервуар для обробки шкір золою (у '
                                               'чинбарстві); бункер або отвір під топкою для збору '
                                               'попелу.'],
                              'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'ЗОЛЬНИ́К, а́, ч., спец. 1. Яма '
                                                                'або чан для зоління шкір. 2. Те '
                                                                'саме, що зольни́ця.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Зафіксовано в радянський '
                                                                     'період (СУМ-11). Наведено '
                                                                     'для лексикографічної '
                                                                     'прозорості.'}}],
  'зорювати': [ { 'headword': 'зо́рювати',
                  'short_label': 'обробляти землю плугом, орати (недок.)',
                  'gloss': 'plow, cultivate land with a plow (imperf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[ˈzɔrʲʊwɐtɪ]'},
                  'stress': { 'form': 'зо́рювати',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/зорювати'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Означає «обробляти землю плугом, орати» (недоконаний вид; '
                                      'доконаний вид — «зора́ти»). Не плутати з «зорюва́ти» '
                                      '(ночувати просто неба під зорями або не спати вночі).',
                  'meaning': { 'definitions': ['Обробляти землю плугом; орати.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ЗО́РЮВАТИ, юю, юєш, недок., '
                                                                 'ЗОРА́ТИ, рю́, ре́ш, док., перех. '
                                                                 'і без додатка. 1. Обробляти '
                                                                 'землю плугом. 2. Орючи, '
                                                                 'знищувати що-небудь. 3. тільки '
                                                                 'док. Порити землю, наробивши '
                                                                 'заглибин, вибоїн; // перен. '
                                                                 'Укрити зморшками (обличчя і т. '
                                                                 'ін.).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Сільськогосподарський '
                                                                      'термін, зафіксований у '
                                                                      'СУМ-11. Документовано для '
                                                                      'лексикографічної повноти.'}},
                { 'headword': 'зорюва́ти',
                  'short_label': 'ночувати просто неба під зорями; не спати вночі (недок.)',
                  'gloss': 'sleep outdoors under the stars; stay awake at night (imperf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[zɔrʲʊˈwɑtɪ]'},
                  'stress': { 'form': 'зорюва́ти',
                              'source': 'ВТС / Грінченко / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/зорювати'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Означає «ночувати просто неба під зорями, спати на світанку '
                                      'або не спати вночі» (недоконаний вид). Засвідчено у '
                                      'Словнику Грінченка: «Спать на открытом воздухе». Не плутати '
                                      'з «зо́рювати» (орати).',
                  'meaning': { 'definitions': [ 'Ночувати просто неба; спати на зорі, на світанку; '
                                                'не спати вночі.'],
                               'source': 'ВТС / Грінченко / СУМ-11'},
                  'pre_soviet_witness': { 'witness': 'Грінченко (1907–1909)',
                                          'quote': 'Зорювати, -рЮю, -єш, гл. Спать на открытом '
                                                   'воздухе. Літом у нас товар у полі зорює.'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ЗОРЮВА́ТИ, ю́ю, ю́єш, недок. 1. '
                                                                 'Ночувати просто неба. // Спати '
                                                                 'на зорі, на світанку. 2. розм. '
                                                                 'Не спати вночі.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Автентичне народне слово, '
                                                                      'зафіксоване в '
                                                                      'дореволюційній та '
                                                                      'радянській '
                                                                      'лексикографії.'}}],
  'квітчаний': [ { 'headword': 'кві́тчаний',
                   'short_label': 'прикрашений, увінчаний квітами (дієприкм.)',
                   'gloss': 'adorned or decorated with flowers (participle)',
                   'pos': 'participle',
                   'cefr': 'B1',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[ˈkwʲitt͡ʃɐnɪj]'},
                   'stress': { 'form': 'кві́тчаний',
                               'source': 'ВТС / Грінченко / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/квітчаний'},
                   'morphology': {'pos': 'дієприкметник', 'paradigm': {'kind': 'adjective'}},
                   'distinction_note': 'Пасивний дієприкметник минулого часу від дієслова '
                                       '«квітчати»: «прикрашений, увінчаний квітами». Засвідчено у '
                                       'Грінченка: «Квітчаною головою схилишся до неньки». Не '
                                       'плутати з прикметником «квітча́ний» (квітковий).',
                   'meaning': { 'definitions': [ 'Прикрашений, увінчаний або вбраний квітами '
                                                 '(дієприкм. пас. мин. ч. до квітчати).'],
                                'source': 'ВТС / Грінченко / СУМ-11'},
                   'pre_soviet_witness': { 'witness': 'Грінченко (1907–1909)',
                                           'quote': 'Квітчаний, -а, -е. 2) Украшенный цветами. '
                                                    'Квітчаною головою схилишся до неньки.'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'КВІ́ТЧАНИЙ, а, е. Дієпр. пас. '
                                                                  'мин. ч. до квітча́ти.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Традиційна '
                                                                       'дієприкметникова форма, '
                                                                       'зафіксована в СУМ-11.'}},
                 { 'headword': 'квітча́ний',
                   'short_label': 'квітковий (рідко)',
                   'gloss': 'floral, flower-like, consisting of floral scents (rare, adj.)',
                   'pos': 'adj',
                   'cefr': 'B2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[kwʲitˈt͡ʃɑnɪj]'},
                   'stress': { 'form': 'квітча́ний',
                               'source': 'ВТС / Грінченко / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/квітчаний'},
                   'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                   'distinction_note': 'Рідкісний якісно-відносний прикметник: «квітковий, '
                                       'сповнений квіткових пахощів». Засвідчено у класичній '
                                       'літературі (Олекса Стороженко) та в Словнику Грінченка: '
                                       '«Тепленький вітрець зо всього степу несе йому квітчані '
                                       'запахи». Не плутати з дієприкметником «кві́тчаний».',
                   'meaning': { 'definitions': ['Те саме, що квітковий (рідко).'],
                                'source': 'ВТС / Грінченко / СУМ-11'},
                   'pre_soviet_witness': { 'witness': 'Грінченко (1907–1909)',
                                           'quote': 'Квітчаний, -а, -е. 1) Цветочный. Тепленький '
                                                    'вітрець зо всього степу несе йому квітчані '
                                                    'запахи.'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'КВІТЧА́НИЙ, а, е, рідко. Те '
                                                                  'саме, що квіткови́й.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Позначено як рідкісне в '
                                                                       'СУМ-11; наведено класичний '
                                                                       'приклад зі Стороженка.'}}],
  'колонковий': [ { 'headword': 'коло́нковий',
                    'short_label': 'стосовний до колонки (техн., друк.)',
                    'gloss': 'relating to a column (mechanical, geological core drill, newspaper '
                             'column)',
                    'pos': 'adj',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[kɔˈlɔnkɔwɪj]'},
                    'stress': { 'form': 'коло́нковий',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/колонковий'},
                    'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                    'distinction_note': 'Прикметник до «колонка» (технічна або друкарська колонка, '
                                        'бурове колонкове буріння тощо). Не плутати з '
                                        '«колонко́вий» (прикметник до «колоно́к» — сибірський '
                                        'хутровий звірок).',
                    'meaning': { 'definitions': [ 'Стосовний до колонки (технічної, бурової або '
                                                  'друкарської).'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'КОЛО́НКОВИЙ, а, е. Стос. до '
                                                                   'колонки (у 3 знач.).',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Технічний термін, '
                                                                        'зафіксований у СУМ-11.'}},
                  { 'headword': 'колонко́вий',
                    'short_label': 'стосовний до тварини колонок або його хутра',
                    'gloss': 'relating to the Siberian weasel (kolonok) or its fur',
                    'pos': 'adj',
                    'cefr': 'B2',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[kɔlɔnˈkɔwɪj]'},
                    'stress': { 'form': 'колонко́вий',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/колонковий'},
                    'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                    'distinction_note': 'Прикметник до зоологічної назви хижака «колоно́к» (родини '
                                        'куницевих): колонкове хутро, колонковий пензель. Не '
                                        'плутати з «коло́нковий» (від колонка).',
                    'meaning': { 'definitions': [ 'Прикметник до колонок; виготовлений із хутра '
                                                  'колонка.'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'КОЛОНКО́ВИЙ, а, е. Прикм. до '
                                                                   'колоно́к. Колонкове хутро; // '
                                                                   'Вигот. із хутра колонка. '
                                                                   'Колонкова шуба.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Зоологічний та хутровий '
                                                                        'термін, зафіксований у '
                                                                        'СУМ-11.'}}],
  'комірний': [ { 'headword': 'комі́рний',
                  'short_label': 'квартирний; у знач. ім. комірне: плата за найману кімнату '
                                 '(розм.)',
                  'gloss': 'relating to lodging; as noun комі́рне: rent, lodging fee (colloquial)',
                  'pos': 'adj',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[kɔˈmʲirnɪj]'},
                  'stress': { 'form': 'комі́рний',
                              'source': 'ВТС / Грінченко / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/комірний'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Розмовний прикметник від «ко́мора» в значенні квартирний; '
                                      'субстантивоване «комі́рне» означає найманий куток або '
                                      'орендну плату за житло («іти в комірне»). Засвідчено у '
                                      'Грінченка: «Комірне, -ного, с. Плата за квартиру». Не '
                                      'плутати з «комірни́й» (стосовний до комори / зерносховища).',
                  'meaning': { 'definitions': [ 'Те саме, що квартирний; у знач. ім. комірне — '
                                                'наймана кімната або плата за житло.'],
                               'source': 'ВТС / Грінченко / СУМ-11'},
                  'pre_soviet_witness': { 'witness': 'Грінченко (1907–1909)',
                                          'quote': 'Комірне, -ного, с. Плата за квартиру. Брати в '
                                                   'комірне. Принимать на квартиру.'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КОМІ́РНИЙ, а, е, розм. 1. Те '
                                                                 'саме, що кварти́рний. 2. у знач. '
                                                                 'ім. комі́рне, ного, с. Наймана '
                                                                 'кімната, куток. 3. у знач. ім. '
                                                                 'комі́рне, ного, с. Плата за '
                                                                 'найману кімнату, куток.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Побутове слово, зафіксоване '
                                                                      'в СУМ-11 з посиланням на '
                                                                      'класиків (Франко, '
                                                                      'Коцюбинський).'}},
                { 'headword': 'комірни́й',
                  'short_label': 'стосовний до комори (зерносховища); комірник',
                  'gloss': 'relating to a granary/storehouse; as noun: storekeeper',
                  'pos': 'adj',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[kɔmʲirˈnɪj]'},
                  'stress': { 'form': 'комірни́й',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/комірний'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Означає «стосовний до комори (зерносховища чи комори для '
                                      'речей)»: комірне вікно, комірний шкідник; субстантивовано — '
                                      '«комірник». Не плутати з «комі́рний» (квартирний, комірне).',
                  'meaning': { 'definitions': [ 'Прикметник до комора; який живе або зберігається '
                                                'в коморі; рідко у знач. ім. — комірник.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КОМІРНИ́Й, а́, е́. 1. Прикм. до '
                                                                 'комо́ра. Сонячний пил просівався '
                                                                 'крізь комірне віконце (Тют., '
                                                                 'Вир, 1964, 380); Комірне '
                                                                 'зберігання насіння; // Який живе '
                                                                 'в коморі. 2. у знач. ім. '
                                                                 'комірни́й, но́го, ч., рідко. Те '
                                                                 'саме, що комірни́к.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Зафіксовано в СУМ-11 як '
                                                                      'пряме похідне від '
                                                                      'комо́ра.'}}],
  'комірниця': [ { 'headword': 'комі́рниця',
                   'short_label': 'квартирантка, жінка-наймачка кутка (розм.)',
                   'gloss': 'female lodger, tenant, subtenant (colloquial)',
                   'pos': 'noun',
                   'cefr': 'B2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[kɔˈmʲirnɪt͡sʲɐ]'},
                   'stress': { 'form': 'комі́рниця',
                               'source': 'ВТС / Грінченко / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/комірниця'},
                   'morphology': { 'pos': 'іменник',
                                   'paradigm': { 'kind': 'noun',
                                                 'gender': 'feminine',
                                                 'animacy': 'animate'}},
                   'distinction_note': 'Розмовне слово на позначення квартирантки (жіночий рід до '
                                       '«комі́рник» — квартирант). Засвідчено у Словнику '
                                       'Грінченка: «Комірниця, -ці, ж. Квартирантка». Не плутати з '
                                       'професійною назвою «комірни́ця» (жінка-завідувачка комори '
                                       'або складу).',
                   'meaning': { 'definitions': [ 'Жінка, що винаймає помешкання, кімнату чи куток; '
                                                 'квартирантка (розм., жін. до комі́рник).'],
                                'source': 'ВТС / Грінченко / СУМ-11'},
                   'pre_soviet_witness': { 'witness': 'Грінченко (1907–1909)',
                                           'quote': 'Комірниця, -ці, ж. Квартирантка. Вх. Зн. 27.'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'КОМІ́РНИЦЯ, і, ж., розм. Жін. '
                                                                  'до комі́рник.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Побутова назва '
                                                                       'квартирантки, засвідчена в '
                                                                       'СУМ-11 цитатою зі '
                                                                       'Стельмаха.'}},
                 { 'headword': 'комірни́ця',
                   'short_label': 'завідувачка комори або складу',
                   'gloss': 'female warehouse keeper, storekeeper (fem. of комірни́к)',
                   'pos': 'noun',
                   'cefr': 'B2',
                   'heritage_status': { 'classification': 'standard',
                                        'is_russianism': False,
                                        'russian_shadow': False,
                                        'vesum_attested': True},
                   'pronunciation': {'ipa': '[kɔmʲirˈnɪt͡sʲɐ]'},
                   'stress': { 'form': 'комірни́ця',
                               'source': 'ВТС / СУМ-11',
                               'url': 'https://slovnyk.me/dict/vts/комірниця'},
                   'morphology': { 'pos': 'іменник',
                                   'paradigm': { 'kind': 'noun',
                                                 'gender': 'feminine',
                                                 'animacy': 'animate'}},
                   'distinction_note': 'Означає працівницю, що завідує коморою або складом (жін. '
                                       'до «комірни́к»). Не плутати з «комі́рниця» (квартирантка).',
                   'meaning': { 'definitions': [ 'Працівниця, яка завідує коморою, складом або '
                                                 'матеріальними цінностями (жін. до комірни́к).'],
                                'source': 'ВТС / СУМ-11'},
                   'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                    'definition': 'КОМІРНИ́ЦЯ, і, ж. Жін. до '
                                                                  'комірни́к.',
                                                    'sovietization_risk': 0,
                                                    'keywords': [],
                                                    'historical_note': 'Професійна назва, '
                                                                       'зафіксована в СУМ-11.'}}],
  'консерваторка': [ { 'headword': 'консерва́торка',
                       'short_label': 'прихильниця консерватизму (жін. до консерва́тор)',
                       'gloss': 'female conservative, supporter of conservatism',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': { 'classification': 'standard',
                                            'is_russianism': False,
                                            'russian_shadow': False,
                                            'vesum_attested': True},
                       'pronunciation': {'ipa': '[kɔnserˈwɑtɔrkɐ]'},
                       'stress': { 'form': 'консерва́торка',
                                   'source': 'ВТС / СУМ-11',
                                   'url': 'https://slovnyk.me/dict/vts/консерваторка'},
                       'morphology': { 'pos': 'іменник',
                                       'paradigm': { 'kind': 'noun',
                                                     'gender': 'feminine',
                                                     'animacy': 'animate'}},
                       'distinction_note': 'Жіночий відповідник до «консерва́тор»: прихильниця '
                                           'політичного чи світоглядного консерватизму, '
                                           'прихильниця збереження традиційних підвалин. Не '
                                           'плутати з «консервато́рка» (студентка або викладачка '
                                           'консерваторії).',
                       'meaning': { 'definitions': [ 'Жінка консервативних поглядів; прихильниця '
                                                     'консерватизму (жін. до консерва́тор).'],
                                    'source': 'ВТС / СУМ-11'},
                       'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                        'definition': 'КОНСЕРВА́ТОРКА, и, ж. Жін. '
                                                                      'до консерва́тор.',
                                                        'sovietization_risk': 0,
                                                        'keywords': [],
                                                        'historical_note': 'Суспільно-політичний '
                                                                           'термін, зафіксований у '
                                                                           'СУМ-11.'}},
                     { 'headword': 'консервато́рка',
                       'short_label': 'студентка або вихованка консерваторії (розм.)',
                       'gloss': 'female conservatory student or graduate (colloquial)',
                       'pos': 'noun',
                       'cefr': 'B2',
                       'heritage_status': { 'classification': 'standard',
                                            'is_russianism': False,
                                            'russian_shadow': False,
                                            'vesum_attested': True},
                       'pronunciation': {'ipa': '[kɔnserwɐˈtɔrkɐ]'},
                       'stress': { 'form': 'консервато́рка',
                                   'source': 'ВТС / СУМ-11',
                                   'url': 'https://slovnyk.me/dict/vts/консерваторка'},
                       'morphology': { 'pos': 'іменник',
                                       'paradigm': { 'kind': 'noun',
                                                     'gender': 'feminine',
                                                     'animacy': 'animate'}},
                       'distinction_note': 'Розмовне слово: студентка або випускниця музичної '
                                           'консерваторії (жін. до «консервато́рець»). Засвідчено '
                                           'у класичній літературі: Леся Українка («У мене сестра '
                                           'консерваторка»). Не плутати з «консерва́торка» '
                                           '(прихильниця консерватизму).',
                       'meaning': { 'definitions': [ 'Студентка або викладачка вищого музичного '
                                                     'навчального закладу — консерваторії (розм., '
                                                     'жін. до консервато́рець).'],
                                    'source': 'ВТС / СУМ-11'},
                       'pre_soviet_witness': { 'witness': 'Леся Українка (1902)',
                                               'quote': '— У мене сестра консерваторка (Л. Укр., '
                                                        'III, 1952, 616).'},
                       'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                        'definition': 'КОНСЕРВАТО́РКА, и, ж., '
                                                                      'розм. Жін. до '
                                                                      'консервато́рець. — У мене '
                                                                      'сестра консерваторка (Л. '
                                                                      'Укр., III, 1952, 616).',
                                                        'sovietization_risk': 0,
                                                        'keywords': [],
                                                        'historical_note': 'Зафіксовано в СУМ-11 з '
                                                                           'автентичною цитатою з '
                                                                           'Лесі Українки.'}}],
  'консерваторський': [ { 'headword': 'консерва́торський',
                          'short_label': 'стосовний до консерватора або консерватизму',
                          'gloss': 'conservative, relating to a conservative or conservatism',
                          'pos': 'adj',
                          'cefr': 'B2',
                          'heritage_status': { 'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                          'pronunciation': {'ipa': '[kɔnserˈwɑtɔrsʲkɪj]'},
                          'stress': { 'form': 'консерва́торський',
                                      'source': 'ВТС / СУМ-11',
                                      'url': 'https://slovnyk.me/dict/vts/консерваторський'},
                          'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                          'distinction_note': 'Прикметник до політичного чи ідеологічного '
                                              '«консерва́тор» (консерваторські погляди, позиція). '
                                              'Не плутати з «консервато́рський» (стосовний до '
                                              'музичної консерваторії).',
                          'meaning': { 'definitions': [ 'Прикметник до консерватор; властивий '
                                                        'консерваторові або консерватизму.'],
                                       'source': 'ВТС / СУМ-11'},
                          'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'КОНСЕРВА́ТОРСЬКИЙ, а, е. '
                                                                         'Прикм. до консерва́тор.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Суспільно-політичний '
                                                                              'прикметник, '
                                                                              'зареєстрований у '
                                                                              'СУМ-11.'}},
                        { 'headword': 'консервато́рський',
                          'short_label': 'стосовний до музичної консерваторії',
                          'gloss': 'relating to a music conservatory',
                          'pos': 'adj',
                          'cefr': 'B2',
                          'heritage_status': { 'classification': 'standard',
                                               'is_russianism': False,
                                               'russian_shadow': False,
                                               'vesum_attested': True},
                          'pronunciation': {'ipa': '[kɔnserwɐˈtɔrsʲkɪj]'},
                          'stress': { 'form': 'консервато́рський',
                                      'source': 'ВТС / СУМ-11',
                                      'url': 'https://slovnyk.me/dict/vts/консерваторський'},
                          'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                          'distinction_note': 'Означає «стосовний до консерваторії (вищого '
                                              'музичного закладу)»: консерваторські студенти, '
                                              'консерваторські традиції. Не плутати з '
                                              '«консерва́торський» (від ідейного консерватора).',
                          'meaning': { 'definitions': [ 'Те саме, що консерваторний; який '
                                                        'стосується консерваторії (музичного '
                                                        'закладу).'],
                                       'source': 'ВТС / СУМ-11'},
                          'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                           'definition': 'КОНСЕРВАТО́РСЬКИЙ, а, е. '
                                                                         'Те саме, що '
                                                                         'консервато́рний. '
                                                                         'Консерваторські '
                                                                         'студенти.',
                                                           'sovietization_risk': 0,
                                                           'keywords': [],
                                                           'historical_note': 'Музично-освітній '
                                                                              'термін, '
                                                                              'зафіксований у '
                                                                              'СУМ-11.'}}],
  'копчення': [ { 'headword': 'ко́пчення',
                  'short_label': 'процес копчення (вудження) харчових продуктів',
                  'gloss': 'smoking, curing food with smoke (action, verbal noun)',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[ˈkɔpt͡ʃenʲːɐ]'},
                  'stress': { 'form': 'ко́пчення',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/копчення'},
                  'morphology': { 'pos': 'іменник',
                                  'paradigm': { 'kind': 'noun',
                                                'gender': 'neuter',
                                                'animacy': 'inanimate'}},
                  'distinction_note': 'Означає дію, процес копчення або вудження продукту '
                                      '(віддієслівний іменник від «копти́ти»). Не плутати з '
                                      '«копче́ння» (збірний іменник: самі копчені вироби, '
                                      'копченина).',
                  'meaning': { 'definitions': [ "Дія за значенням коптити; вудження м'яса, риби "
                                                'тощо.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КО́ПЧЕННЯ, я, с. Дія за знач. '
                                                                 'копти́ти; вудження.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Кулінарний і харчовий '
                                                                      'термін, зафіксований у '
                                                                      'СУМ-11.'}},
                { 'headword': 'копче́ння',
                  'short_label': 'копчені продукти, копченина (збірн.)',
                  'gloss': 'smoked meats or fish, smoked products (collective noun)',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[kɔpˈt͡ʃɛnʲːɐ]'},
                  'stress': { 'form': 'копче́ння',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/копчення'},
                  'morphology': { 'pos': 'іменник',
                                  'paradigm': { 'kind': 'noun',
                                                'gender': 'neuter',
                                                'animacy': 'inanimate'}},
                  'distinction_note': 'Збірне значення: «копчені продукти, копченина» (копчені '
                                      "ковбаси, риба, м'ясо). Не плутати з віддієслівним "
                                      'процесуальним іменником «ко́пчення» (сам процес вудження).',
                  'meaning': { 'definitions': [ 'Копчені харчові продукти; те саме, що копченина '
                                                '(збірн.).'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КОПЧЕ́ННЯ, я, с., збірн. Те '
                                                                 'саме, що копчени́на.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Збірний іменник на '
                                                                      'позначення копчених '
                                                                      'продуктів, зафіксований у '
                                                                      'СУМ-11.'}}],
  'корівник': [ { 'headword': 'корі́вник',
                  'short_label': 'хлів, приміщення для утримання корів (неіст.)',
                  'gloss': 'cowshed, barn for cows, cattle shed (inanimate)',
                  'pos': 'noun',
                  'cefr': 'B1',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[kɔˈrʲiwnɪk]'},
                  'stress': { 'form': 'корі́вник',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/корівник'},
                  'morphology': { 'pos': 'іменник',
                                  'paradigm': { 'kind': 'noun',
                                                'gender': 'masculine',
                                                'animacy': 'inanimate'}},
                  'distinction_note': 'Неістота (чоловічий рід): спеціальне приміщення або хлів '
                                      'для утримання великої рогатої худоби (корівня). Не плутати '
                                      'з «корівни́к» (істота: працівник, доглядач корів).',
                  'meaning': { 'definitions': [ 'Те саме, що корівня; приміщення для утримання '
                                                'корів.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КОРІ́ВНИК, а, ч. Те саме, що '
                                                                 'корі́вня. Бачив його в '
                                                                 'корівнику, де він оглядав корів '
                                                                 'і розмовляв з доярками (Донч., '
                                                                 'V, 1957, 39).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Тваринницький термін для '
                                                                      'господарської будівлі, '
                                                                      'зафіксований у СУМ-11.'}},
                { 'headword': 'корівни́к',
                  'short_label': 'доглядач корів, працівник ферми (іст.)',
                  'gloss': 'cowherd, cattleman, worker tending cows (animate)',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': False},
                  'pronunciation': {'ipa': '[kɔrʲiwˈnɪk]'},
                  'stress': { 'form': 'корівни́к',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/корівник'},
                  'morphology': { 'pos': 'іменник',
                                  'paradigm': { 'kind': 'noun',
                                                'gender': 'masculine',
                                                'animacy': 'animate'}},
                  'distinction_note': 'Істота: працівник ферми, який доглядає корів (чоловічий '
                                      'рід; жіночий відповідник — корівниця). Засвідчено у ВТС та '
                                      'СУМ-11. У VESUM як окрема лема істоти не виділений '
                                      '(зареєстрований тільки як неістота `корі́вник`), тому '
                                      'позначений `vesum_attested: false`. Не плутати з '
                                      'приміщенням «корі́вник».',
                  'meaning': { 'definitions': [ 'Той, хто доглядає корів; робітник на '
                                                'молочнотоварній фермі.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КОРІВНИ́К, а, ч. Той, хто '
                                                                 'доглядає корів.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Професійна назва робітника '
                                                                      'тваринництва, зареєстрована '
                                                                      'в СУМ-11.'}}],
  'коровий': [ { 'headword': 'ко́ровий',
                 'short_label': 'стосовний до інфекційної хвороби кір (мед.)',
                 'gloss': 'measles-related, relating to measles (medical)',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': { 'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                 'pronunciation': {'ipa': '[ˈkɔrɔwɪj]'},
                 'stress': { 'form': 'ко́ровий',
                             'source': 'ВТС / СУМ-11',
                             'url': 'https://slovnyk.me/dict/vts/коровий'},
                 'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                 'distinction_note': 'Медичний термін: стосовний до вірусного інфекційного '
                                     'захворювання «кір» (корове захворювання, корова вакцина). Не '
                                     'плутати з «корови́й» (стосовний до кори головного мозку).',
                 'meaning': { 'definitions': [ 'Медичний термін: стосовний до інфекційної хвороби '
                                               'кір.'],
                              'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'КО́РОВИЙ, а, е, мед. Стос. до '
                                                                'кору. Корове захворювання.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Медичний прикметник від '
                                                                     'іменника кір, зафіксований у '
                                                                     'СУМ-11.'}},
               { 'headword': 'корови́й',
                 'short_label': 'стосовний до кори головного мозку (анат.)',
                 'gloss': 'cortical, relating to the cerebral cortex (anatomy)',
                 'pos': 'adj',
                 'cefr': 'B2',
                 'heritage_status': { 'classification': 'standard',
                                      'is_russianism': False,
                                      'russian_shadow': False,
                                      'vesum_attested': True},
                 'pronunciation': {'ipa': '[kɔrɔˈwɪj]'},
                 'stress': { 'form': 'корови́й',
                             'source': 'ВТС / СУМ-11',
                             'url': 'https://slovnyk.me/dict/vts/коровий'},
                 'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                 'distinction_note': 'Анатомічний термін: стосовний до кори великих півкуль '
                                     'головного мозку (корові центри, корові клітини). Не плутати '
                                     'з «ко́ровий» (стосовний до кору).',
                 'meaning': { 'definitions': [ 'Анатомічний термін: стосовний до кори головного '
                                               'мозку.'],
                              'source': 'ВТС / СУМ-11'},
                 'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                  'definition': 'КОРОВИ́Й, а́, е́. Стос. до кори '
                                                                'головного мозку. Корові центри.',
                                                  'sovietization_risk': 0,
                                                  'keywords': [],
                                                  'historical_note': 'Анатомічний термін від '
                                                                     'іменника кора (головного '
                                                                     'мозку), зафіксований у '
                                                                     'СУМ-11.'}}],
  'креснути': [ { 'headword': 'кре́снути',
                  'short_label': 'тріскаючись, зрушувати з місця про кригу (недок.)',
                  'gloss': 'crack and start breaking up, shift (of ice on river, imperf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[ˈkrɛsnʊtɪ]'},
                  'stress': { 'form': 'кре́снути',
                              'source': 'ВТС / Грінченко / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/креснути'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                  'distinction_note': 'Недоконаний вид: «тріскаючись, ламаючись, зрушувати з місця '
                                      '(про річкову кригу)». Засвідчено у Словнику Грінченка: «О '
                                      'льдѣ: трескаясь трогаться. Крига почала креснути». Не '
                                      'плутати з «кресну́ти» (доконаний вид, однократна дія: '
                                      'викресати іскру).',
                  'meaning': { 'definitions': [ 'Тріскаючись, ламаючись, зрушувати з місця (про '
                                                'річкову кригу під час льодоходу).'],
                               'source': 'ВТС / Грінченко / СУМ-11'},
                  'pre_soviet_witness': { 'witness': 'Грінченко (1907–1909)',
                                          'quote': 'Креснути, -не, гл. О льдѣ: трескаясь '
                                                   'трогаться. Крига почала креснути. Черк. у.'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КРЕ́СНУТИ, не, недок. '
                                                                 'Тріскаючись, ламаючись, '
                                                                 'зрушувати з місця (про кригу). '
                                                                 'Крига почала креснути (Сл. Гр.).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Автентичне народне дієслово '
                                                                      'недоконаного виду, '
                                                                      'зафіксоване в СУМ-11 за '
                                                                      'Словником Грінченка.'}},
                { 'headword': 'кресну́ти',
                  'short_label': 'однократно ударити крицею по кременю, викресати іскру (док.)',
                  'gloss': 'strike a spark with flint and steel, strike once (perf.)',
                  'pos': 'verb',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[krɛsˈnutɪ]'},
                  'stress': { 'form': 'кресну́ти',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/креснути'},
                  'morphology': { 'pos': 'дієслово',
                                  'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                  'distinction_note': 'Доконаний вид (однократна дія до «креса́ти»): ударити '
                                      'кременем по сталі (криці), висікти іскру; раптово блиснути '
                                      'або гнівно глянути. Не плутати з «кре́снути» (недоконаний '
                                      'вид: про скресання криги).',
                  'meaning': { 'definitions': [ 'Однократна дія до кресати: ударити кременем або '
                                                'крицею, викресати іскру; черкнути, раптово '
                                                'блиснути.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'КРЕСНУ́ТИ, ну́, не́ш, док., '
                                                                 'перех. і неперех. Однокр. до '
                                                                 'креса́ти 1, 2, 4. Чумак.. дістав '
                                                                 'з кишені гаман, набив люльку '
                                                                 'тютюну, взяв губку та крицю, '
                                                                 'креснув — і викресав (Україна.., '
                                                                 'І, 1960, 67).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Традиційне однократне '
                                                                      'дієслово до кресати, '
                                                                      'зафіксоване в СУМ-11.'}}],
  'ламповий': [ { 'headword': 'ла́мповий',
                  'short_label': 'стосовний до лампи або електронних ламп (прикм.)',
                  'gloss': 'relating to a lamp or vacuum tube, valve (adj.)',
                  'pos': 'adj',
                  'cefr': 'B1',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[ˈlɑmpɔwɪj]'},
                  'stress': { 'form': 'ла́мповий',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/ламповий'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Прикметник від «ла́мпа»: лампове скло, ламповий '
                                      'радіоприймач чи генератор, що працює на електронних лампах. '
                                      'Не плутати з «лампови́й» (субстантивований іменник: '
                                      'доглядач шахтарських ламп).',
                  'meaning': { 'definitions': [ 'Прикметник до лампа; який діє за допомогою '
                                                'електричних або електронних ламп.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ЛА́МПОВИЙ, а, е. Прикм. до '
                                                                 'ла́мпа. Склозаводи, на яких '
                                                                 'лампове скло виробляють ручним '
                                                                 'способом, будуть цілком '
                                                                 'механізовані (Наука.., 1,1957, '
                                                                 '6); // Який діє за допомогою '
                                                                 'ламп (у 2 знач.). Сучасна '
                                                                 'електротехніка широко '
                                                                 'використовує для створення '
                                                                 'електричних коливань лампові '
                                                                 'генератори (Осн. радіотехн., '
                                                                 '1957, 104).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Загальновживаний прикметник '
                                                                      'технічного та побутового '
                                                                      'вжитку в СУМ-11.'}},
                { 'headword': 'лампови́й',
                  'short_label': 'доглядач і роздавальник шахтарських ламп на копальні (іменник)',
                  'gloss': 'lamp-tender, worker in charge of miners lamps at a colliery (noun)',
                  'pos': 'noun',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': False},
                  'pronunciation': {'ipa': '[lɐmpɔˈwɪj]'},
                  'stress': { 'form': 'лампови́й',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/ламповий'},
                  'morphology': { 'pos': 'іменник',
                                  'paradigm': { 'kind': 'noun',
                                                'gender': 'masculine',
                                                'animacy': 'animate'}},
                  'distinction_note': 'Субстантивований іменник (істота, відмінюється за '
                                      'прикметниковим типом): робітник, який завідує ламповою на '
                                      'шахті, перевіряє та видає лампи шахтарям. Засвідчено у ВТС '
                                      'та СУМ-11. У VESUM зареєстрований лише як прикметник, тому '
                                      'як субстантивований іменник позначений `vesum_attested: '
                                      'false`. Не плутати з прикметником «ла́мповий».',
                  'meaning': { 'definitions': [ 'Робітник, який видає лампи, відповідає за лампове '
                                                'господарство (звичайно на шахті).'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'ЛАМПОВИ́Й, во́го, ч. Робітник, '
                                                                 'який видає лампи, відповідає за '
                                                                 'лампове господарство (звичайно '
                                                                 'на шахті). Тільки на цій шахті '
                                                                 'він працює шістнадцять років. '
                                                                 'Починав з лампового (Рад. Укр., '
                                                                 '27. IX 1961, 2).',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Гірничо-професійний '
                                                                      'субстантивований іменник, '
                                                                      'зафіксований у СУМ-11.'}}],
  'логік': [ { 'headword': 'ло́гік',
               'short_label': 'фахівець із логіки, учений (іст.)',
               'gloss': 'logician, scholar or specialist in logic (animate noun)',
               'pos': 'noun',
               'cefr': 'B2',
               'heritage_status': { 'classification': 'standard',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': True},
               'pronunciation': {'ipa': '[ˈlɔɦʲik]'},
               'stress': { 'form': 'ло́гік',
                           'source': 'ВТС / СУМ-11',
                           'url': 'https://slovnyk.me/dict/vts/логік'},
               'morphology': { 'pos': 'іменник',
                               'paradigm': { 'kind': 'noun',
                                             'gender': 'masculine',
                                             'animacy': 'animate'}},
               'distinction_note': 'Істота: учений, спеціаліст або викладач логіки як філософської '
                                   'дисципліни. Не плутати з «логі́к» (словниковий варіант до '
                                   'лотік / жолоб для води).',
               'meaning': { 'definitions': ['Учений, фахівець із логіки.'],
                            'source': 'ВТС / СУМ-11'},
               'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ЛО́ГІК, а, ч. Учений, фахівець із '
                                                              'логіки.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Науковий термін, зафіксований '
                                                                   'у СУМ-11.'}},
             { 'headword': 'логі́к',
               'short_label': 'відкритий жолоб для стікання води, лотік (словн., рідко)',
               'gloss': 'chute, trough, flume for flowing water (variant/corruption of лотік)',
               'pos': 'noun',
               'cefr': 'C1',
               'heritage_status': { 'classification': 'rare',
                                    'is_russianism': False,
                                    'russian_shadow': False,
                                    'vesum_attested': False},
               'pronunciation': {'ipa': '[lɔˈɦʲik]'},
               'stress': { 'form': 'логі́к',
                           'source': 'СУМ-11',
                           'url': 'https://slovnyk.me/dict/vts/логік'},
               'morphology': { 'pos': 'іменник',
                               'paradigm': { 'kind': 'noun',
                                             'gender': 'masculine',
                                             'animacy': 'inanimate'}},
               'distinction_note': 'Зафіксовано в лексикографічних реєстрах (СУМ-11: «ЛОГІ́К, '
                                   'тока́, ч.») як рідкісний варіант/спотворення слова «лотік» '
                                   '(відкритий жолоб для стікання води, помольний канал водяного '
                                   'млина). У VESUM відсутній через статус варіанта від «лотік» '
                                   '(`vesum_attested: false`). Не плутати з «ло́гік» '
                                   '(учений-логік).',
               'meaning': { 'definitions': [ 'Відкритий жолоб для стікання води, зсипання '
                                             'чого-небудь; канал на водяному млині (варіант до '
                                             'лотік).'],
                            'source': 'СУМ-11'},
               'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                'definition': 'ЛОГІ́К, тока́, ч. 1. Відкритий '
                                                              'жолоб для стікання води, зсипання '
                                                              'чого-небудь. 2. тільки мн. Канали '
                                                              'на водяному млині, греблі тощо, '
                                                              'якими тече вода.',
                                                'sovietization_risk': 0,
                                                'keywords': [],
                                                'historical_note': 'Лексикографічний запис у '
                                                                   'СУМ-11, де форма наводиться з '
                                                                   'парадигмою «тока́» (варіант '
                                                                   'або спотворення від лотік).'}}],
  'лупати': [ { 'headword': 'лу́пати',
                'short_label': 'кліпати очима; миготіти про зірки (розм., недок.)',
                'gloss': 'blink, bat eyelids; twinkle, flicker of stars (colloquial, imperf.)',
                'pos': 'verb',
                'cefr': 'B1',
                'heritage_status': { 'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                'pronunciation': {'ipa': '[ˈlupɐtɪ]'},
                'stress': { 'form': 'лу́пати',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/лупати'},
                'morphology': { 'pos': 'дієслово',
                                'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': 'Означає «кліпати повіками або очима» («лупати очима»), або '
                                    'переносно — світити слабким, нерівним, миготливим світлом '
                                    '(про зірки). Не плутати з «лупа́ти» (відбивати частини від '
                                    'цілого каменю, розбивати скелю: «Лупайте сю скалу!»).',
                'meaning': { 'definitions': [ 'Те саме, що кліпати (очима); переносно — світити '
                                              'слабким миготливим світлом (про зірки).'],
                             'source': 'ВТС / СУМ-11'},
                'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ЛУ́ПАТИ, аю, аєш, недок., фам. 1. '
                                                               'Те саме, що клі́пати 1. — Га-а?.. '
                                                               '— гакнув на всю хату Яків, '
                                                               'підводячи голову і лупаючи своїми '
                                                               'сонними віями (Мирний, І, 1954, '
                                                               '199). ◊ Лу́пати очи́ма див. о́ко. '
                                                               '2. перен. Світити слабким, '
                                                               'нерівним, миготливим світлом (про '
                                                               'зірки тощо).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Розмовне дієслово на '
                                                                    'позначення кліпання очима, '
                                                                    'зафіксоване в СУМ-11 з '
                                                                    'класичними ілюстраціями.'}},
              { 'headword': 'лупа́ти',
                'short_label': 'відбивати, дробити скалу, колупати (недок.)',
                'gloss': 'hew, break off, chip stone or rock, pick at (imperf.)',
                'pos': 'verb',
                'cefr': 'B2',
                'heritage_status': { 'classification': 'standard',
                                     'is_russianism': False,
                                     'russian_shadow': False,
                                     'vesum_attested': True},
                'pronunciation': {'ipa': '[luˈpɑtɪ]'},
                'stress': { 'form': 'лупа́ти',
                            'source': 'ВТС / СУМ-11',
                            'url': 'https://slovnyk.me/dict/vts/лупати'},
                'morphology': { 'pos': 'дієслово',
                                'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                'distinction_note': 'Відоме класичне франкове дієслово: «відбивати частини від '
                                    'скелі чи цілого каменю, колоти твердь, здирати шар» («Лупайте '
                                    'сю скалу! Нехай ні жар, ні холод Не спинить Вас!» Івана '
                                    'Франка). Не плутати з «лу́пати» (кліпати очима).',
                'meaning': { 'definitions': [ 'Відбивати частини від цілого; колупати; віддирати '
                                              'верхній шар; розбиваючи, ламати.'],
                             'source': 'ВТС / СУМ-11'},
                'pre_soviet_witness': { 'witness': 'Іван Франко (1878)',
                                        'quote': 'Лупайте сю скалу! Нехай ні жар, ні холод Не '
                                                 'спинить Вас!'},
                'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                 'definition': 'ЛУПА́ТИ, а́ю, а́єш, недок., перех. '
                                                               'Відбивати частини від цілого; '
                                                               'колупати (у 1 знач.). [Козаки:] '
                                                               'Ой, лучче [краще] б ми, запорожці, '
                                                               'Круту гору лупали, Ніж у тюрмі, у '
                                                               'кайданах, Шість літ пропадали '
                                                               '(Н.-Лев., II, 1956, 465); "Лупайте '
                                                               'сю скалу! Нехай ні жар, ні холод '
                                                               'Не спинить Вас!" (Фр., X, 1954, '
                                                               '48).',
                                                 'sovietization_risk': 0,
                                                 'keywords': [],
                                                 'historical_note': 'Класичне українське дієслово, '
                                                                    'популяризоване поезією Івана '
                                                                    'Франка «Каменярі».'}}],
  'нарізний': [ { 'headword': 'на́різний',
                  'short_label': "окремий, поодинокий, не зв'язаний з іншими",
                  'gloss': 'separate, distinct, disconnected from others, individual',
                  'pos': 'adj',
                  'cefr': 'B2',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[ˈnɑrʲiznɪj]'},
                  'stress': { 'form': 'на́різний',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/нарізний'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': "Означає «окремий, поодинокий, не зв'язаний з іншими»: "
                                      '«серед нарізних покликів» (Михайло Коцюбинський), '
                                      '«нарізними підемо ми шляхами» (Адам Міцкевич у перекладі '
                                      'Максима Рильського). Не плутати з технічним терміном '
                                      '«нарізни́й» (зі спіральними або гвинтовими нарізами).',
                  'meaning': { 'definitions': [ "Окремий, поодинокий, не зв'язаний з іншими; "
                                                'інший, не один і той самий.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НА́РІЗНИЙ, а, е. Окремий, '
                                                                 'поодинокий, не зв’язаний з '
                                                                 'іншими. Тихович не знав уже, як '
                                                                 'покласти кінець тій прикрій '
                                                                 'сцені, коли враз почув, що в '
                                                                 'юрмі починає притихати, а серед '
                                                                 'нарізних покликів молдуван '
                                                                 'співучий голос пана писаря бере '
                                                                 'гору над затихаючою бурею '
                                                                 '(Коцюб., І, 1955, 204); // '
                                                                 'Інший, не один і той самий.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Літературний прикметник зі '
                                                                      'значенням відокремленості, '
                                                                      'зафіксований у СУМ-11.'}},
                { 'headword': 'нарізни́й',
                  'short_label': 'з гвинтовою нарізкою, різьбленням (техн., військ.)',
                  'gloss': 'rifled (of barrel, weapon), threaded (of bolt, screw), tapped',
                  'pos': 'adj',
                  'cefr': 'B1',
                  'heritage_status': { 'classification': 'standard',
                                       'is_russianism': False,
                                       'russian_shadow': False,
                                       'vesum_attested': True},
                  'pronunciation': {'ipa': '[nɐrʲizˈnɪj]'},
                  'stress': { 'form': 'нарізни́й',
                              'source': 'ВТС / СУМ-11',
                              'url': 'https://slovnyk.me/dict/vts/нарізний'},
                  'morphology': {'pos': 'прикметник', 'paradigm': {'kind': 'adjective'}},
                  'distinction_note': 'Технічний та військовий термін: який має спіральні нарізи '
                                      'або гвинтове різьблення (нарізна зброя, нарізний ствол, '
                                      'нарізні болти, нарізні комбайни). Не плутати з «на́різний» '
                                      '(окремий, відокремлений).',
                  'meaning': { 'definitions': [ 'Який має на своїй поверхні або в каналі нарізи '
                                                '(гвинтове різьблення); який використовують для '
                                                'нарізування.'],
                               'source': 'ВТС / СУМ-11'},
                  'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                   'definition': 'НАРІЗНИ́Й, а́, е́, спец. 1. Який '
                                                                 'має на своїй поверхні нарізи. У '
                                                                 'Волгограді вчені і новатори '
                                                                 'розробили і освоїли випуск '
                                                                 'азбоцементних труб з нарізкою і '
                                                                 'нарізними муфтами (Роб. газ., '
                                                                 '25.11 1966, 2). 2. Який '
                                                                 'використовують для нарізування. '
                                                                 'Нарізні комбайни.',
                                                   'sovietization_risk': 0,
                                                   'keywords': [],
                                                   'historical_note': 'Технічний і військовий '
                                                                      'термін, зафіксований у '
                                                                      'СУМ-11.'}}],
  'находитися': [ { 'headword': 'нахо́дитися',
                    'short_label': 'виявлятися, бути в наявності; знаходитися (недок.)',
                    'gloss': 'be found, be present, turn up; be born (colloquial, imperf.)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[nɐˈxɔdɪtɪsʲɐ]'},
                    'stress': { 'form': 'нахо́дитися',
                                'source': 'ВТС / Грінченко / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/находитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'недоконаний'}},
                    'distinction_note': 'Недоконаний вид (парне до «найти́ся»): «бути в наявності, '
                                        'виявлятися, знаходитися». Засвідчено у Тараса Шевченка: '
                                        '«Може найдеться дівоче серце, карі очі, що заплачуть на '
                                        'сі думи...». Не плутати з «находи́тися» (доконаний вид: '
                                        'походити досхочу, втомитися від тривалої ходьби).',
                    'meaning': { 'definitions': [ 'Бути в наявності; виявлятися, траплятися; розм. '
                                                  '— народжуватися (парне до найтися).'],
                                 'source': 'ВТС / Грінченко / СУМ-11'},
                    'pre_soviet_witness': { 'witness': 'Грінченко (1907–1909)',
                                            'quote': 'Находитися, -джуся, -дишся, сов. в. найтися, '
                                                     '-йдУся, -дешся, гл. 1) Находиться, найтися. '
                                                     'Може найдеться дівоче серце, карі очі, що '
                                                     'заплачуть на сі думи... Шевч. 2) Только сов. '
                                                     'в. Родиться.'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'НАХО́ДИТИСЯ, джуся, дишся, '
                                                                   'недок., НАЙТИ́СЯ, найду́ся, '
                                                                   'на́йдешся, док. 1. Бути в '
                                                                   'наявності. Не находилось ні '
                                                                   'одної [дівчини], котра б '
                                                                   'пригорнула його, як старша '
                                                                   'сестра (Мирний, IV, 1955, '
                                                                   '169). // Виявлятися, '
                                                                   'траплятися. 2. тільки док., '
                                                                   'розм. Те саме, що народи́тися.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Засвідчено в СУМ-11 з '
                                                                        'багатими цитатами з '
                                                                        'класичної літератури '
                                                                        '(Мирний, Вовчок, Леся '
                                                                        'Українка).'}},
                  { 'headword': 'находи́тися',
                    'short_label': 'походити багато, досхочу, втомитися від ходіння (док.)',
                    'gloss': "walk a lot, walk to one's heart's content; grow tired from walking "
                             '(perf.)',
                    'pos': 'verb',
                    'cefr': 'B1',
                    'heritage_status': { 'classification': 'standard',
                                         'is_russianism': False,
                                         'russian_shadow': False,
                                         'vesum_attested': True},
                    'pronunciation': {'ipa': '[nɐxɔˈdɪtɪsʲɐ]'},
                    'stress': { 'form': 'находи́тися',
                                'source': 'ВТС / СУМ-11',
                                'url': 'https://slovnyk.me/dict/vts/находитися'},
                    'morphology': { 'pos': 'дієслово',
                                    'paradigm': {'kind': 'verb', 'aspect': 'доконаний'}},
                    'distinction_note': 'Доконаний вид (розмовне): «походити багато, досхочу; '
                                        'втомитися від ходіння» («Вже так находився Іванко по '
                                        'Новгороду, що й ноги не носили»). Не плутати з '
                                        '«нахо́дитися» (недоконаний вид: бути в наявності, '
                                        'виявлятися).',
                    'meaning': { 'definitions': [ 'Походити багато, досхочу; походивши багато, '
                                                  'стомитися (док., розм.).'],
                                 'source': 'ВТС / СУМ-11'},
                    'soviet_colonization_context': { 'source': 'СУМ-11 (1970–1980)',
                                                     'definition': 'НАХОДИ́ТИСЯ, ходжу́ся, '
                                                                   'хо́дишся, док., розм. Походити '
                                                                   'багато, досхочу. — По '
                                                                   'світлоньці ходжу, Та й не '
                                                                   'находжуся (Нар. лірика, 1956, '
                                                                   '180). // Походивши багато, '
                                                                   'стомитися.',
                                                     'sovietization_risk': 0,
                                                     'keywords': [],
                                                     'historical_note': 'Розмовне доконане '
                                                                        'дієслово зі значенням '
                                                                        'вичерпної тривалої дії, '
                                                                        'зафіксоване в СУМ-11.'}}]}
