"""Ukrainian Verb Deep Mechanics Practice Engine (Дієслово).

Implements Ukrainian Pravopys 2019:
  - Part III: Морфологія — Дієслово (офіційне видання НАН України / Інститут мовознавства):
    * § 115: Дійсний спосіб. Дієвідміни (I та II дієвідміни), особові закінчення теперішнього
      й простого майбутнього часів:
      - I дієвідміна: закінчення -еш/-єш, -емо/-ємо, -ете/-єте, 3-тя особа множини: -уть/-ють.
      - II дієвідміна: закінчення -иш/-їш, -имо/-їмо, -ите/-їте, 3-тя особа множини: -ать/-ять.
      - Чергування приголосних при дієвідмінюванні:
        * Вставний [л'] після губних б, п, в, м, ф перед голосними в 1 ос. однини та 3 ос. множини II дієвідміни
          (любити -> люблю, люблять; спати -> сплю, сплять).
        * Чергування зубних і шиплячих у 1-й особі однини дієслів II дієвідміни: д -> дж (ходити -> ходжу),
          т -> ч (летіти -> лечу), с -> ш (просити -> прошу), з -> ж (возити -> вожу), ст -> щ (мостити -> мощу),
          зд -> ждж (їздити -> їжджу).
        * Чергування приголосних та голосних в основах дієслів I дієвідміни: с -> ш (писати -> пишу),
          к -> ч (пекти -> печу, печеш), г -> ж (могти -> можу, можеш), а -> е (брати -> беру), терти -> труть.
      - Видові пари дієслів: недоконаний та доконаний вид (способи творення: префіксація, суфіксація,
        чергування голосних о <-> а в корені: допомогти <-> допомагати, перемогти <-> перемагати; суплетивізм).
    * § 116: Наказовий спосіб:
      - Проста форма 2-ї особи однини та множини: закінчення -и / -іть (під наголосом або після більшості збігів
        приголосних: роби, робіть, пиши, пишіть) vs нульове закінчення / -те (читай, читайте, стань, станьте, вірте).
      - Форми 1-ї особи множини (заохочення до спільної дії): закінчення -мо / -імо (ходімо, робімо, читаймо).
      - Усунення русизмів: заміна кальок «давай(те) робити / підемо» на нормативні форми (ходімо, зробімо).
    * § 119: Дієприкметник:
      - Творення пасивних дієприкметників минулого часу на -ний / -тий (написаний, зроблений, розбитий, відкритий).
      - Усунення активних дієприкметників теперішнього часу на -ачий/-ячий/-учий/-ючий (*бажаючий* -> охочий,
        *діючий* -> чинний, *початкуючий* -> початківець).
      - Незмінювані безособові присудкові форми на -но / -то (зроблено, виконано, ухвалено, відкрито).
    * § 120: Дієприслівник:
      - Недоконаний вид: суфікси -учи / -ючи (I дієвідміна) та -ачи / -ячи (II дієвідміна): читаючи, пишучи, сидячи.
      - Доконаний вид: суфікси -вши / -ши: прочитавши, написавши, принісши, лігши.

Provides structured pedagogical feedback explaining the specific rule and misconception,
and guarantees zero collisions among options.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sqlite3
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class VerbCategory(StrEnum):
    """Categories of Ukrainian verb deep mechanics practice."""

    CONJ_CLASS_I_VOWEL_E_YE = "conj_class_i_vowel_e_ye"
    CONJ_CLASS_II_VOWEL_Y_YI = "conj_class_ii_vowel_y_yi"
    CONJ_LABIAL_EPENTHESIS_L = "conj_labial_epenthesis_l"
    CONJ_DENTAL_MUTATION_1SG = "conj_dental_mutation_1sg"
    CONJ_STEM_MUTATION_CLASS_I = "conj_stem_mutation_class_i"
    ASPECT_PREFIXATION = "aspect_prefixation"
    ASPECT_SUFFIXATION_ABLAUT = "aspect_suffixation_ablaut"
    ASPECT_SUPPLETIVE = "aspect_suppletive"
    IMPERATIVE_SYNTHETIC_ENDINGS = "imperative_synthetic_endings"
    IMPERATIVE_INCLUSIVE_1PL = "imperative_inclusive_1pl"
    IMPERATIVE_ANTI_CALQUE_DAVAI = "imperative_anti_calque_davai"
    PARTICIPLE_PASSIVE_FORMATION = "participle_passive_formation"
    PARTICIPLE_ANTI_CALQUE_ACTIVE = "participle_anti_calque_active"
    PARTICIPLE_IMPERSONAL_NO_TO = "participle_impersonal_no_to"
    GERUND_FORMATION_ASPECT = "gerund_formation_aspect"


class VerbInterferenceType(StrEnum):
    """Taxonomy of morphological, phonological, and syntactic verb misconceptions."""

    FALSE_CONJUGATION_CLASS_I_FOR_II = "false_conjugation_class_i_for_ii"
    FALSE_CONJUGATION_CLASS_II_FOR_I = "false_conjugation_class_ii_for_i"
    FALSE_LABIAL_MISSING_EPENTHESIS_L = "false_labial_missing_epenthesis_l"
    FALSE_DENTAL_MISSING_MUTATION_1SG = "false_dental_missing_mutation_1sg"
    FALSE_STEM_MUTATION_CLASS_I = "false_stem_mutation_class_i"
    FALSE_ASPECT_PREFIX_CONFUSION = "false_aspect_prefix_confusion"
    FALSE_ASPECT_IMPERFECTIVATION_ABLAUT = "false_aspect_imperfectivation_ablaut"
    FALSE_ASPECT_SUPPLETIVE_REGULARIZED = "false_aspect_suppletive_regularized"
    FALSE_IMPERATIVE_MISSING_Y_ENDING = "false_imperative_missing_y_ending"
    FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING = "false_imperative_excessive_y_ending"
    FALSE_IMPERATIVE_1PL_RUSSIAN_TE = "false_imperative_1pl_russian_te"
    FALSE_IMPERATIVE_INDICATIVE_CONFUSION = "false_imperative_indicative_confusion"
    RUSSIAN_CALQUE_DAVAI_IMPERATIVE = "russian_calque_davai_imperative"
    FALSE_PARTICIPLE_SUFFIX_NYI_TYI = "false_participle_suffix_nyi_tyi"
    RUSSIAN_CALQUE_ACTIVE_PARTICIPLE = "russian_calque_active_participle"
    FALSE_IMPERSONAL_FORMS_AGREEMENT = "false_impersonal_forms_agreement"
    FALSE_GERUND_ASPECT_SUFFIX = "false_gerund_aspect_suffix"


INTERFERENCE_EXPLANATIONS: dict[VerbInterferenceType, dict[str, str]] = {
    VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II: {
        "ua": "Помилка дієвідміни: для дієслова I дієвідміни помилково вжито закінчення II дієвідміни. За Правописом 2019 § 115, дієслова I дієвідміни в особових закінченнях мають голосний -е- (-є-) (пишеш, чуєш, бореться, чеше) та закінчення 3-ї особи множини -уть (-ють) (пишуть, борються, мелють), а не -и-/-ї- чи -ать/-ять.",
        "en": "Conjugation class error: Class II endings erroneously applied to a Class I verb. Under Pravopys 2019 § 115, Class I verbs take vowel -e- (-ye-) in personal endings (pyshesh, boretsia) and 3rd person plural -ut / -yut (pyshyt, boriutsia, meliut), not -y-/-yi- or -at/-iat.",
    },
    VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I: {
        "ua": "Помилка дієвідміни: для дієслова II дієвідміни помилково вжито закінчення I дієвідміни. За Правописом 2019 § 115, дієслова II дієвідміни в особових закінченнях мають голосний -и- (-ї-) (летиш, сидить, стоїмо) та закінчення 3-ї особи множини -ать (-ять) (летять, сидять, стоять, біжать), а не -е-/-є- чи -уть/-ють.",
        "en": "Conjugation class error: Class I endings erroneously applied to a Class II verb. Under Pravopys 2019 § 115, Class II verbs take vowel -y- (-yi-) in personal endings (letysh, sydyt, stoimo) and 3rd person plural -at / -iat (letiat, sydiat, stoiat, bizhat), not -e-/-ye- or -ut/-yut.",
    },
    VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L: {
        "ua": "Порушення правил милозвучності та чергування (Правопис 2019 § 115): після губних приголосних б, п, в, м, ф перед голосними в 1-й особі однини та 3-й особі множини II дієвідміни обов'язково з'являється вставний [л'] (любити -> люблю, люблять; спати -> сплю, сплять; ловити -> ловлю, ловлять).",
        "en": "Missing epenthetic consonant [l'] after labials b, p, v, m, f (Pravopys 2019 § 115). In the 1st person singular and 3rd person plural of Class II verbs, epenthetic [l'] is strictly required (liubyty -> liubliu, liubliat; spaty -> spliu, spliat).",
    },
    VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG: {
        "ua": "Помилка у чергуванні приголосних у 1-й особі однини II дієвідміни (Правопис 2019 § 115): зубні та шиплячі зазнають закономірного чергування (д -> дж: ходити -> ходжу; т -> ч: летіти -> лечу; с -> ш: просити -> прошу; з -> ж: возити -> вожу; ст -> щ: мостити -> мощу; зд -> ждж: їздити -> їжджу). Форми на зразок *ходю, *летю, *просю є грубою помилкою.",
        "en": "Missing dental/alveolar consonant alternation in 1st person singular of Class II verbs (Pravopys 2019 § 115): d -> dzh (khodyty -> khodzhy), t -> ch (letity -> lechu), s -> sh (prosyty -> proshu), z -> zh (vozyty -> vozhu), st -> shch (mostyty -> moshchu), zd -> zhdzh (yizdyty -> yizhdzhu). Forms like *khodiu or *letiu are non-standard.",
    },
    VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I: {
        "ua": "Помилка в основі теперішнього часу дієслів I дієвідміни (Правопис 2019 § 115): кінцеві приголосні та голосні інфінітивної основи зазнають закономірних чергувань (писати -> пишу, пишеш; чесати -> чешу, чеше; пекти -> печу, печеш; могти -> можу, можеш; брати -> беру; терти -> труть). Не можна зберігати незмінну інфінітивну основу (*писаю, *чесає, *пеку, *могу).",
        "en": "Stem mutation error in Class I present tense (Pravopys 2019 § 115). Stem-final consonants and root vowels undergo historical mutations (pysaty -> pyshu, pyshesh; chesaty -> cheshe; pekty -> pechu; mohty -> mozhu; braty -> beru; terty -> trut). Preserving the unmutated infinitive stem (*pysaiu, *chesaie, *peku) is erroneous.",
    },
    VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION: {
        "ua": "Помилка у виборі видової пари: утворення доконаного виду префіксальним способом вимагає нормативного префікса для конкретного дієслова (писати -> написати, робити -> зробити, малювати -> намалювати). Інші префікси змінюють лексичне значення дієслова або утворюють ненормативні семантичні зв'язки.",
        "en": "Aspectual prefix error: forming the perfective partner requires the specific normative prefix (pysaty -> napysaty, robyty -> zrobyty, maliuvaty -> namaliuvaty). Using alternative prefixes alters lexical semantics or forms incorrect collocations.",
    },
    VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT: {
        "ua": "Помилка у чергуванні голосних при вторинній імперфективації (Правопис 2019 § 115): при утворенні дієслів недоконаного виду за допомогою суфіксів -а- / -ува- кореневий голосний [о] чергується з [а] (допомогти -> допомагати, перемогти -> перемагати, зламати -> зламувати). Вживання форми без чергування (*допомогати, *перемогати) є грубим суржиком.",
        "en": "Missing root vowel ablaut in imperfectivation (Pravopys 2019 § 115). In secondary imperfective formation with suffixes -a- / -uva-, root vowel [o] alternates with [a] (dopomohty -> dopomahaty, peremohty -> peremahaty). Forms without alternation (*dopomahaty) are non-standard surzhyk.",
    },
    VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED: {
        "ua": "Помилка у суплетивній видовій парі: дієслова цієї групи творять видові пари від різних коренів (брати <-> взяти, говорити <-> сказати, ловити <-> піймати, класти <-> покласти). Спроба утворити доконаний вид суфіксами чи префіксами від початкового кореня (*збрати, *поговорити у значенні сказати) порушує нормативне співвідношення нейтральної видової пари.",
        "en": "Suppletive aspect error: specific verbs form aspectual pairs using distinct historical stems (braty <-> vziaty, hovoryty <-> skazaty, lovyty <-> piimaty, klasty <-> poklasty). Regular prefixation of the imperfective base (*zbraty) does not form the canonical neutral pair.",
    },
    VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING: {
        "ua": "Помилка у творенні наказового способу (Правопис 2019 § 116): дієслова з наголосом на закінченні або зі збігом приголосних у кінці основи переважно мають закінчення -и у 2-й особі однини та -іть у множині (роби, робіть; пиши, пишіть; мовчи, мовчіть; неси, несіть; пор. винятки на зразок чисть, морщ). Усічення закінчення (*пиш, *мовч) є ненормативним.",
        "en": "Missing mandatory imperative ending -y / -it (Pravopys 2019 § 116). Verbs with ending stress or stem-final consonant clusters generally take ending -y in 2sg and -it in 2pl (roby, robit; pyshy, pyshit; movchy, movchit; cf. exceptions like chyst, morshch). Truncation (*pysh) is incorrect.",
    },
    VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING: {
        "ua": "Помилка у творенні наказового способу (Правопис 2019 § 116): дієслова з основою на голосний (після якого стоїть [j]) або на м'який чи губний приголосний без наголосу на закінченні мають нульове закінчення у 2-й особі однини та -те у множині (читай, читайте; стань, станьте; сядь, сядьте; вір, вірте). Додавання закінчення -и (*читаї, *станій) є помилкою.",
        "en": "Excessive imperative ending -y (Pravopys 2019 § 116). Stems ending in vowels + /j/ or soft consonants with non-final stress take zero ending in 2sg and -te in 2pl (chytai, chytaite; stan, stante; vir, virte). Adding extra endings is non-standard.",
    },
    VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE: {
        "ua": "Русифікована форма наказового способу: в українській літературній мові форма 1-ї особи множини (заклик до спільної дії) за Правописом 2019 § 116 має закінчення -мо або -імо (ходімо, робімо, читаймо, працюймо, напишімо). Приєднання частки або закінчення -те (*ходімте, *робімте, *пішли) є запозиченням з російської мови і суперечить нормі.",
        "en": "Russian-influenced imperative 1pl error. Under Pravopys 2019 § 116, Ukrainian forms encouragement to joint action with endings -mo / -imo (khodimo, robimo, chytaimo, pratsiuimo, napyshimo). Appending *-te (*khodimte, *robimte, *pishly) is a Russianism.",
    },
    VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION: {
        "ua": "Помилка способу дієслова: вжито форму дійсного способу (теперішнього чи майбутнього часу) замість форми наказового способу. За Правописом 2019 § 116, наказ або заклик до спільної дії вимагає синтетичних форм наказового способу (пишіть, ходімо, робімо, читаймо), а не форм дійсного способу (пишете, ходимо, робимо, читаємо).",
        "en": "Mood error: indicative mood form erroneously used instead of imperative. Under Pravopys 2019 § 116, commands or joint encouragements require imperative forms (pyshit, khodimo, robimo, chytaimo), not indicative forms (pyshete, khodymo, robymo, chytaiemo).",
    },
    VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE: {
        "ua": "Груба синтаксична калька з російської мови. Сполучення слова «давай / давайте» з інфінітивом або формою майбутнього часу (*давай підемо, *давайте робити) є ненормативним. В українській мові вживаються питомі синтетичні форми наказового способу: «ходімо!», «робімо!», «почнімо!», «працюймо!» (Правопис 2019 § 116).",
        "en": "Severe Russian syntactic calque. Combinations of 'davai / davaite' + infinitive or future (*davai pidemo, *davaite robyty) are non-standard. Ukrainian uses native synthetic 1st person plural imperative forms: 'khodimo!', 'robimo!', 'pochnimo!' (Pravopys 2019 § 116).",
    },
    VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI: {
        "ua": "Помилка у суфіксі пасивного дієприкметника (Правопис 2019 § 119): основа дієслова визначає вибір суфікса -ний (-ений, -єний) або -тий. Дієслова з односкладовою основою на голосний та дієслова на -ерти, -олоти творять форму на -тий (розбитий, відкритий, тертий, зшитий), тоді як більшість інших дієслів вимагають -ний (написаний, зроблений, вивчений).",
        "en": "Passive participle suffix error (Pravopys 2019 § 119). Verb stem determines suffix -nyi (-enyi, -yisnyi) vs -tyi. Monosyllabic stems ending in vowels and stems in -erty take -tyi (rozbytyi, vidkrytyi, zshytyi), whereas standard polysyllabic stems take -nyi (napysanyi, zroblenyi).",
    },
    VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE: {
        "ua": "Порушення синтаксичних і словотвірних норм: в українській літературній мові слова на -ачий/-ячий/-учий/-ючий переважно функціонують як прикметники або іменники (квітучий, живучий, стоячий per Правопис 2019 § 119). Вживання активних дієприкметників теперішнього часу для вираження процесуальної ознаки (*бажаючий*, *діючий закон*, *початкуючий автор*) є калькою з російської мови. Їх слід замінювати прикметниками, іменниками або підрядними реченнями: охочий / той, хто бажає; чинний закон; початківець.",
        "en": "Active present participle calque. While Ukrainian recognizes lexicalized adjectival forms in -achy/-uchy (kvituchyi, zhyvuchyi per Pravopys 2019 § 119), using them as verbal active participles (*bazhaiuchyi, *diiuchyi) is an alien calque. Replace with proper adjectives, agent nouns, or relative clauses: okhochyi, chynnyi, pochatkivets.",
    },
    VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT: {
        "ua": "Помилка у вживанні безособової форми на -но / -то (Правопис 2019 § 119): у безособових реченнях присудок передається незмінюваною формою на -но / -то з прямим додатком у знахідному відмінку (роботу виконано, закон прийнято, двері відчинено). Вживання узгодженого дієприкметника зі зв'язкою (*була виконана робота) є калькою з пасивних конструкцій російської мови.",
        "en": "Impersonal -no / -to form error (Pravopys 2019 § 119). Impersonal state constructions require invariant verbal forms in -no / -to with the direct object in the accusative (robotu vykonano, zakon pryiniato). Using personal agreeing participles (*bula vykonana robota) is a calque of Russian passive syntax.",
    },
    VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX: {
        "ua": "Помилка у творенні дієприслівника (Правопис 2019 § 120): для вираження одночасної дії (недоконаний вид) вживаються суфікси -учи/-ючи (I дієвідміна) та -ачи/-ячи (II дієвідміна) (читаючи, сидячи). Для вираження передуючої дії (доконаний вид) вживається суфікс -вши/-ши (прочитавши, принісши). Не можна вживати -вши для одночасної дії або -ючи для завершеної.",
        "en": "Gerund aspectual suffix error (Pravopys 2019 § 120). Imperfective simultaneous actions use -uchy/-iuchy (Class I) or -achy/-iachy (Class II) (chytaiuchy, sydyachy). Prior completed actions use -vshy/-shy (prochytaffshy, prynisshy). Confusing these markers breaks aspectual concordance.",
    },
}


@dataclass(frozen=True)
class VerbDistractor:
    text: str
    interference_type: VerbInterferenceType
    explanation: dict[str, str]


@dataclass(frozen=True)
class VerbCard:
    card_id: str
    category: VerbCategory
    cefr_level: str
    prompt_sentence: str
    blank_target: str
    correct_answer: str
    distractors: list[VerbDistractor]
    pravopys_section: str
    rule_summary: dict[str, str]

    def all_options(self) -> list[str]:
        """Return all options shuffled deterministically by card_id sha256."""
        opts = [self.correct_answer] + [d.text for d in self.distractors]
        seed_int = int(hashlib.sha256(self.card_id.encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed_int)
        rng.shuffle(opts)
        return opts

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "category": self.category.value,
            "cefr_level": self.cefr_level,
            "prompt_sentence": self.prompt_sentence,
            "blank_target": self.blank_target,
            "correct_answer": self.correct_answer,
            "options": self.all_options(),
            "distractors": [
                {
                    "text": d.text,
                    "interference_type": d.interference_type.value,
                    "explanation": d.explanation,
                }
                for d in self.distractors
            ],
            "pravopys_section": self.pravopys_section,
            "rule_summary": self.rule_summary,
        }


def resolve_conjugation_class_rule(category: VerbCategory) -> tuple[str, str, str]:
    """Resolve diagnostic indicator and bilingual explanation for conjugation class per Правопис 2019 § 115."""
    if category == VerbCategory.CONJ_CLASS_I_VOWEL_E_YE:
        return (
            "-е- / -є- (-уть / -ють)",
            "I дієвідміна: дієслова мають закінчення 3-ї особи множини -уть/-ють та голосний -е-/-є- в особових закінченнях (пишеш, знаєш, борються, мелють, чеше).",
            "Conjugation Class I: 3rd person plural ends in -ut/-yut and personal endings take -e-/-ye- (pyshesh, znaiesh, boriutsia, meliut, cheshe).",
        )
    if category == VerbCategory.CONJ_CLASS_II_VOWEL_Y_YI:
        return (
            "-и- / -ї- (-ать / -ять)",
            "II дієвідміна: дієслова мають закінчення 3-ї особи множини -ать/-ять та голосний -и-/-ї- в особових закінченнях (летиш, сидить, стоїмо, біжать).",
            "Conjugation Class II: 3rd person plural ends in -at/-iat and personal endings take -y-/-yi- (letysh, sydyt, stoimo, bizhat).",
        )
    raise ValueError(f"Category {category} is not a primary conjugation class category.")


def resolve_epenthesis_rule() -> tuple[str, str, str]:
    """Resolve epenthesis indicator and explanation per Правопис 2019 § 115."""
    return (
        "[л']",
        "Вставний [л'] після губних приголосних б, п, в, м, ф перед голосними в 1 ос. однини та 3 ос. множини II дієвідміни (любити -> люблю, люблять; спати -> сплю, сплять).",
        "Epenthetic [l'] after labials b, p, v, m, f in 1sg and 3pl of Class II verbs (liubyty -> liubliu, liubliat; spaty -> spliu, spliat).",
    )


def resolve_dental_mutation_rule(mutation_key: str) -> tuple[str, str, str]:
    """Resolve dental/alveolar consonant alternation rule for 1sg per Правопис 2019 § 115."""
    mapping = {
        "d_dzh": ("д -> дж", "д чергується з дж: ходити -> ходжу, садити -> саджу.", "d alternates with dzh: khodyty -> khodzhy."),
        "t_ch": ("т -> ч", "т чергується з ч: летіти -> лечу, платити -> плачу.", "t alternates with ch: letity -> lechu."),
        "s_sh": ("с -> ш", "с чергується з ш: просити -> прошу, косити -> кошу.", "s alternates with sh: prosyty -> proshu."),
        "z_zh": ("з -> ж", "з чергується з ж: возити -> вожу, морозити -> морожу.", "z alternates with zh: vozyty -> vozhu."),
        "st_shch": ("ст -> щ", "ст чергується зі щ: мостити -> мощу, чистити -> чищу.", "st alternates with shch: mostyty -> moshchu."),
        "zd_zhdzh": ("зд -> ждж", "зд чергується з ждж: їздити -> їжджу.", "zd alternates with zhdzh: yizdyty -> yizhdzhu."),
    }
    if mutation_key not in mapping:
        raise ValueError(f"Unknown dental mutation key: {mutation_key}")
    return mapping[mutation_key]


def resolve_imperative_rule(stem_type: str) -> tuple[str, str, str]:
    """Resolve imperative mood ending rule per Правопис 2019 § 116."""
    if stem_type == "stressed_or_cluster":
        return (
            "-и / -іть",
            "Під наголосом або після більшості збігів приголосних закінчення -и у 2-й особі однини та -іть у множині (роби, робіть; пиши, пишіть; пор. винятки морщ, чисть).",
            "Under stress or following consonant clusters, ending is typically -y (2sg) and -it (2pl) (roby, robit; pyshy, pyshit; cf. exceptions morshch, chyst).",
        )
    if stem_type == "vowel_or_soft":
        return (
            "нульове / -те",
            "Після голосних та м'яких приголосних без кінцевого наголосу виступає нульове закінчення у 2-й особі однини та -те у множині (читай, читайте; стань, станьте).",
            "After vowels or non-final-stressed soft consonants, zero ending in 2sg and -te in 2pl (chytai, chytaite; stan, stante).",
        )
    if stem_type == "inclusive_1pl":
        return (
            "-мо / -імо",
            "Форми 1-ї особи множини наказового способу (заклик до спільної дії) мають нормативні закінчення -мо або -імо (ходімо, робімо, читаймо).",
            "1st person plural imperative (encouragement to joint action) takes native endings -mo or -imo (khodimo, robimo, chytaimo).",
        )
    raise ValueError(f"Unknown imperative stem type: {stem_type}")


def resolve_participle_anti_calque_rule() -> tuple[str, str, str]:
    """Resolve active participle anti-calque rule per Правопис 2019 § 119."""
    return (
        "Подолання активних дієприкметників",
        "Активні дієприкметники теперішнього часу на -ачий/-ячий/-учий/-ючий замінюються прикметниками, іменниками чи підрядними реченнями (охочий, чинний).",
        "Active present participles in -achy/-uchy are replaced with proper adjectives, agent nouns, or subordinate clauses (okhochyi, chynnyi).",
    )


def resolve_impersonal_form_rule() -> tuple[str, str, str]:
    """Resolve impersonal predicate rule per Правопис 2019 § 119."""
    return (
        "-но / -то",
        "У безособових реченнях присудок виражається незмінюваними дієслівними формами на -но / -то із прямим додатком у знахідному відмінку (роботу виконано, закон прийнято).",
        "Impersonal state predicates require invariant verbal forms ending in -no / -to with the direct object in the accusative (robotu vykonano, zakon pryiniato).",
    )


def resolve_gerund_aspect_rule(aspect: str) -> tuple[str, str, str]:
    """Resolve gerund aspect suffix rule per Правопис 2019 § 120."""
    if aspect == "imperfective":
        return (
            "-учи/-ючи / -ачи/-ячи",
            "Дієприслівники недоконаного виду для одночасної дії творяться за допомогою суфіксів -учи/-ючи (I дієвідміна) або -ачи/-ячи (II дієвідміна) (читаючи, сидячи).",
            "Imperfective gerunds for simultaneous action take suffixes -uchy/-iuchy (Class I) or -achy/-iachy (Class II) (chytaiuchy, sydyachy).",
        )
    if aspect == "perfective":
        return (
            "-вши / -ши",
            "Дієприслівники доконаного виду для передуючої завершеної дії творяться за допомогою суфіксів -вши (після голосних) та -ши (після приголосних) (прочитавши, принісши).",
            "Perfective gerunds for prior completed action take suffixes -vshy (after vowels) and -shy (after consonants) (prochytaffshy, prynisshy).",
        )
    raise ValueError(f"Unknown gerund aspect: {aspect}")


# Curated, academically authoritative cards covering all 15 verb categories
CANONICAL_VERB_CARDS: list[dict[str, Any]] = [
    # =========================================================================
    # 1. CONJ_CLASS_I_VOWEL_E_YE (I дієвідміна: -еш/-єш, -уть/-ють) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_conj_i_borotysia_3pl",
        "category": VerbCategory.CONJ_CLASS_I_VOWEL_E_YE,
        "cefr_level": "A2",
        "prompt_sentence": "Українські захисники мужньо ___ за свободу рідної землі.",
        "blank_target": "борються",
        "correct_answer": "борються",
        "distractors": [
            {
                "text": "боряться",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "боряються",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "борять",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «боротися» належить до I дієвідміни, тому в 3-й особі множини має нормативне закінчення -ють: «борються» (а не *боряться).",
            "en": "The verb 'borotysia' belongs to Class I, taking ending -yut in 3pl: 'boriutsia' (not *boriatsia).",
        },
    },
    {
        "card_id": "verb_conj_i_moloty_3pl",
        "category": VerbCategory.CONJ_CLASS_I_VOWEL_E_YE,
        "cefr_level": "B1",
        "prompt_sentence": "Жорна старого водяного млина без упину ___ свіже зерно.",
        "blank_target": "мелють",
        "correct_answer": "мелють",
        "distractors": [
            {
                "text": "молють",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "молоють",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "мелеть",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «молоти» належить до I дієвідміни з чергуванням голосного в основі: мелю, мелеш, мелють (а не *молотять чи *молють).",
            "en": "The verb 'moloty' belongs to Class I with root ablaut: meliu, melesh, meliut.",
        },
    },
    {
        "card_id": "verb_conj_i_chuty_2sg",
        "category": VerbCategory.CONJ_CLASS_I_VOWEL_E_YE,
        "cefr_level": "A1",
        "prompt_sentence": "Чи ти ___ цей дивовижний спів солов'я у саду?",
        "blank_target": "чуєш",
        "correct_answer": "чуєш",
        "distractors": [
            {
                "text": "чуїш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "чусиш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "чуяш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «чути» належить до I дієвідміни (вони чують), тому у 2-й особі однини має закінчення -єш: «чуєш» (а не *чуїш).",
            "en": "The verb 'chuty' belongs to Class I (chuiut), taking ending -yesh in 2sg: 'chuiesh' (not *chuyish).",
        },
    },
    {
        "card_id": "verb_conj_i_chesaty_3sg",
        "category": VerbCategory.CONJ_CLASS_I_VOWEL_E_YE,
        "cefr_level": "A2",
        "prompt_sentence": "Мати з любов'ю щоранку дбайливо ___ довгі коси своєї доньки.",
        "blank_target": "чеше",
        "correct_answer": "чеше",
        "distractors": [
            {
                "text": "чесає",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "чешить",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "чешає",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «чесати» належить до I дієвідміни з чергуванням с -> ш в основі: чешу, чешеш, чеше (а не *чесає чи *чешить).",
            "en": "The verb 'chesaty' belongs to Class I with s -> sh stem mutation: cheshu, cheshesh, cheshe.",
        },
    },
    {
        "card_id": "verb_conj_i_khotiti_3pl",
        "category": VerbCategory.CONJ_CLASS_I_VOWEL_E_YE,
        "cefr_level": "A1",
        "prompt_sentence": "Студенти щиро ___ якнайшвидше опанувати складну тему.",
        "blank_target": "хочуть",
        "correct_answer": "хочуть",
        "distractors": [
            {
                "text": "хотять",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "хотяють",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "хочуться",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «хотіти» в усіх особових формах належить до I дієвідміни: хочеш, хоче, хочемо, хочете, хочуть (форма *хотять є русизмом).",
            "en": "The verb 'khotity' belongs to Class I in all forms: khochesh, khoche, khochut (not *khotiat).",
        },
    },

    # =========================================================================
    # 2. CONJ_CLASS_II_VOWEL_Y_YI (II дієвідміна: -иш/-їш, -ать/-ять) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_conj_ii_letity_3pl",
        "category": VerbCategory.CONJ_CLASS_II_VOWEL_Y_YI,
        "cefr_level": "A1",
        "prompt_sentence": "Восени перелітні птахи ключ за ключем ___ у вирій.",
        "blank_target": "летять",
        "correct_answer": "летять",
        "distractors": [
            {
                "text": "летуть",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "летіють",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "летють",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «летіти» належить до II дієвідміни (летиш, летить), тому в 3-й особі множини має закінчення -ять: «летять» (а не *летуть).",
            "en": "The verb 'letity' is Class II (letysh, letyt), taking ending -iat in 3pl: 'letiat' (not *letut).",
        },
    },
    {
        "card_id": "verb_conj_ii_kleity_2sg",
        "category": VerbCategory.CONJ_CLASS_II_VOWEL_Y_YI,
        "cefr_level": "A2",
        "prompt_sentence": "Чому ти так квапливо ___ ці старі шпалери на вологу стіну?",
        "blank_target": "клеїш",
        "correct_answer": "клеїш",
        "distractors": [
            {
                "text": "клеєш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "клейош",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "клеяш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «клеїти» належить до II дієвідміни (вони клеять), тому у 2-й особі однини має закінчення -їш: «клеїш» (а не *клеєш).",
            "en": "The verb 'kleity' is Class II (kleiat), taking ending -yish in 2sg: 'kleyish' (not *kleyesh).",
        },
    },
    {
        "card_id": "verb_conj_ii_bihty_3pl",
        "category": VerbCategory.CONJ_CLASS_II_VOWEL_Y_YI,
        "cefr_level": "A1",
        "prompt_sentence": "Діти весело й наввипередки ___ по шовковій зеленій траві.",
        "blank_target": "біжать",
        "correct_answer": "біжать",
        "distractors": [
            {
                "text": "біжуть",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "біжають",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "бігнуть",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «бігти» в українській мові належить до II дієвідміни: біжиш, біжить, біжимо, біжать (а не *біжуть чи *біжають).",
            "en": "The verb 'bihty' belongs to Class II in Ukrainian: bizhysh, bizhyt, bizhat (not *bizhut).",
        },
    },
    {
        "card_id": "verb_conj_ii_stoyaty_3pl",
        "category": VerbCategory.CONJ_CLASS_II_VOWEL_Y_YI,
        "cefr_level": "A1",
        "prompt_sentence": "Вікові дуби велично ___ на високому крутому схилі Дніпра.",
        "blank_target": "стоять",
        "correct_answer": "стоять",
        "distractors": [
            {
                "text": "стоють",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "стойють",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "стояють",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «стояти» належить до II дієвідміни: стоїш, стоїть, стоїмо, стоять (а не *стоють).",
            "en": "The verb 'stoiaty' belongs to Class II: stoish, stoit, stoiat (not *stoiut).",
        },
    },
    {
        "card_id": "verb_conj_ii_spaty_2sg",
        "category": VerbCategory.CONJ_CLASS_II_VOWEL_Y_YI,
        "cefr_level": "A1",
        "prompt_sentence": "Чому ти ще досі не ___, адже вже настала глибока північ?",
        "blank_target": "спиш",
        "correct_answer": "спиш",
        "distractors": [
            {
                "text": "спеш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "сипеш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "спаєш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «спати» належить до II дієвідміни (вони сплять), тому у 2-й особі однини має закінчення -иш: «спиш» (а не *спеш).",
            "en": "The verb 'spaty' belongs to Class II (spliat), taking -ysh in 2sg: 'spysh' (not *spesh).",
        },
    },

    # =========================================================================
    # 3. CONJ_LABIAL_EPENTHESIS_L (Вставний [л'] після б, п, в, м, ф) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_labial_liubyty_3pl",
        "category": VerbCategory.CONJ_LABIAL_EPENTHESIS_L,
        "cefr_level": "A1",
        "prompt_sentence": "Усі щирі українці палко й віддано ___ рідну мову та культуру.",
        "blank_target": "люблять",
        "correct_answer": "люблять",
        "distractors": [
            {
                "text": "люб'ять",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "любять",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "люблють",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Після губного [б] перед закінченням 3-ї особи множини з'являється вставний [л']: «люблять» (а не *люб'ять чи *любять).",
            "en": "After labial [b] before 3pl ending, epenthetic [l'] is strictly required: 'liubliat' (not *liub'iat).",
        },
    },
    {
        "card_id": "verb_labial_spaty_1sg",
        "category": VerbCategory.CONJ_LABIAL_EPENTHESIS_L,
        "cefr_level": "A1",
        "prompt_sentence": "Коли я втомлююся після насиченого робочого дня, я солодко ___ до світанку.",
        "blank_target": "сплю",
        "correct_answer": "сплю",
        "distractors": [
            {
                "text": "спу",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "сп'ю",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "спаю",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Після губного [п] в 1-й особі однини з'являється обов'язковий вставний [л']: «сплю» (а не *спу чи *сп'ю).",
            "en": "After labial [p] in 1sg, epenthetic [l'] is mandatory: 'spliu' (not *spu).",
        },
    },
    {
        "card_id": "verb_labial_lovyty_3pl",
        "category": VerbCategory.CONJ_LABIAL_EPENTHESIS_L,
        "cefr_level": "A2",
        "prompt_sentence": "Досвідчені рибалки вранці на річці вміло ___ сріблясту рибу.",
        "blank_target": "ловлять",
        "correct_answer": "ловлять",
        "distractors": [
            {
                "text": "лов'ять",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "ловять",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "ловуть",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Після губного [в] у формі 3-ї особи множини II дієвідміни обов'язково з'являється вставний [л']: «ловлять» (а не *лов'ять).",
            "en": "After labial [v] in 3pl of Class II, epenthetic [l'] is mandatory: 'lovliat' (not *lov'iat).",
        },
    },
    {
        "card_id": "verb_labial_liapyty_1sg",
        "category": VerbCategory.CONJ_LABIAL_EPENTHESIS_L,
        "cefr_level": "B1",
        "prompt_sentence": "Разом із маленьким сином я старанно ___ фігурки з м'якого пластиліну.",
        "blank_target": "ліплю",
        "correct_answer": "ліплю",
        "distractors": [
            {
                "text": "ліпю",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "ліп'ю",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "ліпаю",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Після губного [п] у дієслові «ліпити» в 1-й особі однини з'являється вставний [л']: «ліплю» (а не *ліпю чи *ліп'ю).",
            "en": "After labial [p] in 'lipity', 1sg requires epenthetic [l']: 'lipliu' (not *lipiu).",
        },
    },
    {
        "card_id": "verb_labial_tyamyty_3pl",
        "category": VerbCategory.CONJ_LABIAL_EPENTHESIS_L,
        "cefr_level": "B2",
        "prompt_sentence": "Ці талановиті науковці чудово ___ у складних математичних формулах.",
        "blank_target": "тямлять",
        "correct_answer": "тямлять",
        "distractors": [
            {
                "text": "тям'ять",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "тямять",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "тямуть",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Після губного [м] у дієслові «тямити» в 3-й особі множини виступає вставний [л']: «тямлять» (а не *тям'ять).",
            "en": "After labial [m] in 'tiamyty', 3pl requires epenthetic [l']: 'tiamliat' (not *tiam'iat).",
        },
    },

    # =========================================================================
    # 4. CONJ_DENTAL_MUTATION_1SG (д->дж, т->ч, с->ш, з->ж, ст->щ, зд->ждж) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_dental_khodyty_1sg",
        "category": VerbCategory.CONJ_DENTAL_MUTATION_1SG,
        "cefr_level": "A1",
        "prompt_sentence": "Щоранку я із великим задоволенням ___ пішки до міського парку.",
        "blank_target": "ходжу",
        "correct_answer": "ходжу",
        "distractors": [
            {
                "text": "ходю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "хожду",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "ходжую",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "У 1-й особі однини дієслів II дієвідміни приголосний [д] закономірно чергується з [дж]: ходити -> «ходжу» (а не *ходю).",
            "en": "In 1sg of Class II verbs, [d] strictly alternates with [dzh]: khodyty -> 'khodzhy' (not *khodiu).",
        },
    },
    {
        "card_id": "verb_dental_letity_1sg",
        "category": VerbCategory.CONJ_DENTAL_MUTATION_1SG,
        "cefr_level": "A1",
        "prompt_sentence": "Завтра вранці я першим рейсом ___ до Львова на наукову конференцію.",
        "blank_target": "лечу",
        "correct_answer": "лечу",
        "distractors": [
            {
                "text": "летю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "летяю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "літю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "У 1-й особі однини дієслова «летіти» приголосний [т] закономірно чергується з [ч]: «лечу» (а не *летю).",
            "en": "In 1sg of 'letity', [t] alternates with [ch]: 'lechu' (not *letiu).",
        },
    },
    {
        "card_id": "verb_dental_prosyty_1sg",
        "category": VerbCategory.CONJ_DENTAL_MUTATION_1SG,
        "cefr_level": "A1",
        "prompt_sentence": "Я щиро й переконливо ___ вас звернути пильну увагу на цю деталь.",
        "blank_target": "прошу",
        "correct_answer": "прошу",
        "distractors": [
            {
                "text": "просю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "прошаю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "просею",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "У 1-й особі однини дієслова «просити» приголосний [с] чергується з [ш]: «прошу» (а не *просю).",
            "en": "In 1sg of 'prosyty', [s] alternates with [sh]: 'proshu' (not *prosiu).",
        },
    },
    {
        "card_id": "verb_dental_vozyty_1sg",
        "category": VerbCategory.CONJ_DENTAL_MUTATION_1SG,
        "cefr_level": "A2",
        "prompt_sentence": "Кожні вихідні я залюбки ___ бабусю на прогулянку до ботанічного саду.",
        "blank_target": "вожу",
        "correct_answer": "вожу",
        "distractors": [
            {
                "text": "возю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "вожду",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "возяю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "У 1-й особі однини дієслова «возити» приголосний [з] чергується з [ж]: «вожу» (а не *возю).",
            "en": "In 1sg of 'vozyty', [z] alternates with [zh]: 'vozhu' (not *voziu).",
        },
    },
    {
        "card_id": "verb_dental_chystyty_1sg",
        "category": VerbCategory.CONJ_DENTAL_MUTATION_1SG,
        "cefr_level": "A2",
        "prompt_sentence": "Щовечора я ретельно й неквапливо ___ зуби спеціальною пастою.",
        "blank_target": "чищу",
        "correct_answer": "чищу",
        "distractors": [
            {
                "text": "чистю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "чистчу",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
            {
                "text": "чищаю",
                "interference_type": VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Збіг приголосних [ст] у 1-й особі однини дієслова «чистити» чергується зі [щ]: «чищу» (а не *чистю).",
            "en": "Consonant cluster [st] in 1sg of 'chystyty' alternates with [shch]: 'chyshchu' (not *chystiu).",
        },
    },

    # =========================================================================
    # 5. CONJ_STEM_MUTATION_CLASS_I (с->ш, к->ч, г->ж, брати->беру) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_stem_pysaty_1sg",
        "category": VerbCategory.CONJ_STEM_MUTATION_CLASS_I,
        "cefr_level": "A1",
        "prompt_sentence": "Зараз я натхненно ___ розгорнутого листа своєму давньому другові.",
        "blank_target": "пишу",
        "correct_answer": "пишу",
        "distractors": [
            {
                "text": "писаю",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "пишю",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "пису",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "В основі дієслова «писати» приголосний [с] чергується з [ш] в усіх формах теперішнього часу: «пишу», «пишеш» (а не *писаю).",
            "en": "In 'pysaty', [s] alternates with [sh] across present forms: 'pyshu', 'pyshesh' (not *pysaiu).",
        },
    },
    {
        "card_id": "verb_stem_pekty_2sg",
        "category": VerbCategory.CONJ_STEM_MUTATION_CLASS_I,
        "cefr_level": "A2",
        "prompt_sentence": "Який смачний святковий пиріг ти сьогодні ___ у печі?",
        "blank_target": "печеш",
        "correct_answer": "печеш",
        "distractors": [
            {
                "text": "пекеш",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "печиш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "пекаєш",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "При відмінюванні дієслова «пекти» приголосний [к] перед голосним [е] чергується з [ч]: «печеш», «пече» (а не *пекеш чи *печиш).",
            "en": "In 'pekty', [k] before [e] alternates with [ch]: 'pechesh', 'peche' (not *pekesh).",
        },
    },
    {
        "card_id": "verb_stem_mohty_2sg",
        "category": VerbCategory.CONJ_STEM_MUTATION_CLASS_I,
        "cefr_level": "A1",
        "prompt_sentence": "Ти неодмінно ___ впоратися з цим важливим творчим завданням.",
        "blank_target": "можеш",
        "correct_answer": "можеш",
        "distractors": [
            {
                "text": "могеш",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "можиш",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "могаєш",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "У дієслові «могти» приголосний [г] перед голосним [е] закономірно чергується з [ж]: «можеш» (а не *могеш).",
            "en": "In 'mohty', [h] before [e] alternates with [zh]: 'mozhesh' (not *mohesh).",
        },
    },
    {
        "card_id": "verb_stem_braty_1sg",
        "category": VerbCategory.CONJ_STEM_MUTATION_CLASS_I,
        "cefr_level": "A1",
        "prompt_sentence": "Щодня я охоче ___ повну відповідальність за свої вчинки.",
        "blank_target": "беру",
        "correct_answer": "беру",
        "distractors": [
            {
                "text": "браю",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "берю",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "браву",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "У дієслові «брати» корінь у формах теперішнього часу має голосний [е]: «беру», «береш» (а не *браю).",
            "en": "In 'braty', root vowel alternates to [e] in present tense: 'beru', 'beresh' (not *braiu).",
        },
    },
    {
        "card_id": "verb_stem_terty_3pl",
        "category": VerbCategory.CONJ_STEM_MUTATION_CLASS_I,
        "cefr_level": "A2",
        "prompt_sentence": "Майстри довго й ретельно ___ сухі фарби у кам'яній ступці.",
        "blank_target": "труть",
        "correct_answer": "труть",
        "distractors": [
            {
                "text": "теруть",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "терють",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "трить",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «терти» в теперішньому часі має випадний голосний [е]: тру, треш, «труть» (а не *теруть чи *терять).",
            "en": "In 'terty', root vowel drops in present tense: tru, tresh, 'trut' (not *terut).",
        },
    },

    # =========================================================================
    # 6. ASPECT_PREFIXATION (Видові пари: префіксація) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_aspect_pref_pysaty_perf",
        "category": VerbCategory.ASPECT_PREFIXATION,
        "cefr_level": "A1",
        "prompt_sentence": "Письменник нарешті повністю ___ завершальний розділ свого роману.",
        "blank_target": "написав",
        "correct_answer": "написав",
        "distractors": [
            {
                "text": "пописав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "списав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "переписав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Нейтральною видовою парою до «писати» для позначення завершеності дії є префікс на-: «написати» (префікс по- означає обмеженість дії в часі, с- — копіювання).",
            "en": "The neutral perfective counterpart to 'pysaty' is 'napysaty'.",
        },
    },
    {
        "card_id": "verb_aspect_pref_robyty_perf",
        "category": VerbCategory.ASPECT_PREFIXATION,
        "cefr_level": "A1",
        "prompt_sentence": "Студент сумлінно та бездоганно ___ все домашнє завдання.",
        "blank_target": "зробив",
        "correct_answer": "зробив",
        "distractors": [
            {
                "text": "наробив",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "поробив",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "проробив",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Нейтральною видовою парою до «робити» є форма з префіксом з-: «зробити» («наробити» має відтінок помилки або надмірної кількості).",
            "en": "The neutral perfective counterpart to 'robyty' is 'zrobyty'.",
        },
    },
    {
        "card_id": "verb_aspect_pref_chytaty_perf",
        "category": VerbCategory.ASPECT_PREFIXATION,
        "cefr_level": "A1",
        "prompt_sentence": "Учора ввечері я вперше від початку до кінця ___ цю захопливу нову книгу (виберіть нейтральну доконану пару до «читати»).",
        "blank_target": "прочитав",
        "correct_answer": "прочитав",
        "distractors": [
            {
                "text": "прочитавав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "почитав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": {
                    "ua": "Префікс по- позначає дію, обмежену в часі («почитав трохи»), а не повне прочитання від початку до кінця.",
                    "en": "The prefix po- denotes action limited in time ('read for a bit'), not complete reading from beginning to end.",
                },
            },
            {
                "text": "прочитив",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": {
                    "ua": "Помилкове застосування суфікса II дієвідміни -ив замість -ав: правильно «прочитав», а не «*прочитив» (Правопис 2019 § 115).",
                    "en": "Erroneous use of Class II suffix -yv instead of -av: standard is 'prochytav', not '*prochytiv' (Pravopys 2019 § 115).",
                },
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Нейтральною видовою парою до «читати» для позначення повністю завершеної дії є «прочитати» з префіксом про- (Правопис 2019 § 115).",
            "en": "The neutral perfective counterpart to 'chytaty' denoting fully completed action is 'prochytaty' with prefix pro- (Pravopys 2019 § 115).",
        },
    },
    {
        "card_id": "verb_aspect_pref_buduvaty_perf",
        "category": VerbCategory.ASPECT_PREFIXATION,
        "cefr_level": "A2",
        "prompt_sentence": "Будівельники успішно та вчасно ___ новий міст через річку.",
        "blank_target": "збудували",
        "correct_answer": "збудували",
        "distractors": [
            {
                "text": "набудували",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "збудовували",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "добудували би",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Канонічною нейтральною видовою парою до «будувати» є форма «збудувати» (збудувати новий міст / дім).",
            "en": "The canonical neutral perfective partner to 'buduvaty' is 'zbuduvaty'.",
        },
    },
    {
        "card_id": "verb_aspect_pref_maliuvaty_perf",
        "category": VerbCategory.ASPECT_PREFIXATION,
        "cefr_level": "A1",
        "prompt_sentence": "Художник за кілька годин натхненно ___ чудовий пейзаж.",
        "blank_target": "намалював",
        "correct_answer": "намалював",
        "distractors": [
            {
                "text": "помалював",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "змалював",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "розмалював",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Нейтральною видовою парою до «малювати» для результату є «намалювати» (змалювати означає скопіювати).",
            "en": "The neutral perfective counterpart to 'maliuvaty' is 'namaliuvaty'.",
        },
    },

    # =========================================================================
    # 7. ASPECT_SUFFIXATION_ABLAUT (Імперфективація, о <-> а) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_aspect_ablaut_dopomahaty",
        "category": VerbCategory.ASPECT_SUFFIXATION_ABLAUT,
        "cefr_level": "A2",
        "prompt_sentence": "Волонтери невтомно ___ літнім людям щотижня долати труднощі.",
        "blank_target": "допомагають",
        "correct_answer": "допомагають",
        "distractors": [
            {
                "text": "допомогають",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "допоможують",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "допомагують",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "При творенні дієслова недоконаного виду «допомагати» від «допомогти» кореневий [о] обов'язково чергується з [а]: «допомагають» (а не *допомогають).",
            "en": "In imperfectivation of 'dopomohty', root [o] mutates to [a]: 'dopomahaiut' (not *dopomohaiut).",
        },
    },
    {
        "card_id": "verb_aspect_ablaut_peremahaty",
        "category": VerbCategory.ASPECT_SUFFIXATION_ABLAUT,
        "cefr_level": "A2",
        "prompt_sentence": "Правда та незламна воля завжди впевнено ___ темряву.",
        "blank_target": "перемагають",
        "correct_answer": "перемагають",
        "distractors": [
            {
                "text": "перемогають",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "переможують",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "перемагують",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово недоконаного виду від «перемогти» твориться з чергуванням о <-> а в корені: «перемагати» / «перемагають» (форма *перемогають — суржик).",
            "en": "Imperfective partner of 'peremohty' requires o <-> a ablaut: 'peremahaty' / 'peremahaiut'.",
        },
    },
    {
        "card_id": "verb_aspect_suff_pysaty_impersuff",
        "category": VerbCategory.ASPECT_SUFFIXATION_ABLAUT,
        "cefr_level": "B1",
        "prompt_sentence": "Секретар уважно ___ важливий офіційний документ за новими вимогами.",
        "blank_target": "переписував",
        "correct_answer": "переписував",
        "distractors": [
            {
                "text": "переписавав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "переписавав би",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "переписав би",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Вторинна імперфективація дієслова «переписати» здійснюється за допомогою суфікса -ува-: «переписувати» / «переписував» (а не *переписавати).",
            "en": "Secondary imperfectivation uses suffix -uva-: 'perepysuvaty' / 'perepysuvav' (not *perepysavaty).",
        },
    },
    {
        "card_id": "verb_aspect_suff_vidkryvaty",
        "category": VerbCategory.ASPECT_SUFFIXATION_ABLAUT,
        "cefr_level": "A2",
        "prompt_sentence": "О дев'ятій ранку працівники щодня урочисто ___ двері музею.",
        "blank_target": "відкривають",
        "correct_answer": "відкривають",
        "distractors": [
            {
                "text": "відкриють",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "відкривлять",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II],
            },
            {
                "text": "відкривують",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Для позначення повторюваної дії у теперішньому часі вживається дієслово недоконаного виду із суфіксом -ва-: «відкривають» (відкриють — майбутній доконаний).",
            "en": "Repetitive present action requires the imperfective with suffix -va-: 'vidkryvaiut' (vidkryiut is future perfective).",
        },
    },
    {
        "card_id": "verb_aspect_ablaut_zlamuvaty",
        "category": VerbCategory.ASPECT_SUFFIXATION_ABLAUT,
        "cefr_level": "B1",
        "prompt_sentence": "Буря безжально ___ сухі гілки старого дерева одну за одною.",
        "blank_target": "зламувала",
        "correct_answer": "зламувала",
        "distractors": [
            {
                "text": "зломила",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "зломувала",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "зломовувала",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово недоконаного виду твориться суфіксом -ува- з чергуванням голосного в основі: «зламувати» / «зламувала» (а не *зломовувала).",
            "en": "Imperfective formation with -uva- and root vowel alternation: 'zlamuvaty' / 'zlamuvala'.",
        },
    },

    # =========================================================================
    # 8. ASPECT_SUPPLETIVE (Суплетивні видові пари) [§ 115]
    # =========================================================================
    {
        "card_id": "verb_aspect_sup_braty_vziaty",
        "category": VerbCategory.ASPECT_SUPPLETIVE,
        "cefr_level": "A1",
        "prompt_sentence": "Хлопець рішуче підійшов і відразу ___ важкий чемодан до рук.",
        "blank_target": "взяв",
        "correct_answer": "взяв",
        "distractors": [
            {
                "text": "збрав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED],
            },
            {
                "text": "побрав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "набрав",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Видова пара «брати» (недок.) <-> «взяти» (док.) є суплетивною. Утворення *збрав є грубою помилкою.",
            "en": "'braty' <-> 'vziaty' is a suppletive aspectual pair; forming *zbrav is erroneous.",
        },
    },
    {
        "card_id": "verb_aspect_sup_hovoryty_skazaty",
        "category": VerbCategory.ASPECT_SUPPLETIVE,
        "cefr_level": "A1",
        "prompt_sentence": "Учитель зачекав тиші в класі й твердо ___ головну новину.",
        "blank_target": "сказав",
        "correct_answer": "сказав",
        "distractors": [
            {
                "text": "поговорив",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "зговорив",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED],
            },
            {
                "text": "виговорив",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Нейтральною видовою парою до «говорити» є суплетивне дієслово «сказати» («поговорити» означає лише провести певну розмову).",
            "en": "The neutral perfective counterpart to 'hovoryty' is suppletive 'skazaty'.",
        },
    },
    {
        "card_id": "verb_aspect_sup_lovyty_piimaty",
        "category": VerbCategory.ASPECT_SUPPLETIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Кіт довго вартував біля нори і врешті миттєво ___ спритну мишу.",
        "blank_target": "піймав",
        "correct_answer": "піймав",
        "distractors": [
            {
                "text": "половлював",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT],
            },
            {
                "text": "зловив би",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "ловляв",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Канонічною видовою парою до «ловити» для позначення завершеного факту захоплення є дієслово «піймати».",
            "en": "The primary perfective partner to 'lovyty' is 'piimaty'.",
        },
    },
    {
        "card_id": "verb_aspect_sup_klasty_poklasty",
        "category": VerbCategory.ASPECT_SUPPLETIVE,
        "cefr_level": "A1",
        "prompt_sentence": "Будь ласка, акуратно ___ важливі папери на мій робочий стіл.",
        "blank_target": "поклади",
        "correct_answer": "поклади",
        "distractors": [
            {
                "text": "положи",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "покладити",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED],
            },
            {
                "text": "кладити",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "В українській мові вживається дієслово «класти» (недок.) та «покласти» (док.). Форма *положи є грубим суржиком.",
            "en": "Standard Ukrainian uses 'klasty' (imp.) and 'poklasty' (perf.). The form *polozhy is a Russianism.",
        },
    },
    {
        "card_id": "verb_aspect_sup_shukaty_znaity",
        "category": VerbCategory.ASPECT_SUPPLETIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Після тривалих архівних досліджень історики нарешті ___ втрачений рукопис.",
        "blank_target": "знайшли",
        "correct_answer": "знайшли",
        "distractors": [
            {
                "text": "відшукали би",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
            {
                "text": "зшукали",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_SUPPLETIVE_REGULARIZED],
            },
            {
                "text": "пошукали",
                "interference_type": VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_ASPECT_PREFIX_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 115",
        "rule_summary": {
            "ua": "Дієслово «знайти» (знайшли) виступає завершеним видовим корелятом до процесу пошуку («шукати»).",
            "en": "'znaity' (znaishly) is the perfective counterpart to ongoing 'shukaty'.",
        },
    },

    # =========================================================================
    # 9. IMPERATIVE_SYNTHETIC_ENDINGS (-и / -іть vs нульове / -те) [§ 116]
    # =========================================================================
    {
        "card_id": "verb_imperative_roby_2sg",
        "category": VerbCategory.IMPERATIVE_SYNTHETIC_ENDINGS,
        "cefr_level": "A1",
        "prompt_sentence": "Завжди чесно й сумлінно ___ свою роботу, хоч би якою складною вона була.",
        "blank_target": "роби",
        "correct_answer": "роби",
        "distractors": [
            {
                "text": "робей",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING],
            },
            {
                "text": "робий",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING],
            },
            {
                "text": "робле",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Дієслово «робити» у 2-й особі однини наказового способу має закінчення -и: «роби» (Правопис 2019 § 116).",
            "en": "The imperative 2sg of 'robyty' strictly takes ending -y: 'roby' (Pravopys 2019 § 116).",
        },
    },
    {
        "card_id": "verb_imperative_pyshy_2pl",
        "category": VerbCategory.IMPERATIVE_SYNTHETIC_ENDINGS,
        "cefr_level": "A1",
        "prompt_sentence": "Шановні колеги, будь ласка, уважно й охайно ___ свої наукові звіти.",
        "blank_target": "пишіть",
        "correct_answer": "пишіть",
        "distractors": [
            {
                "text": "пиште",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING],
            },
            {
                "text": "пишете",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
            {
                "text": "пишайте",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Форма наказового способу 2-ї особи множини від «писати» має закінчення -іть: «пишіть» (форма «пишете» — теперішній час дійсного способу).",
            "en": "Imperative 2pl of 'pysaty' takes ending -it: 'pyshit' (pyshete is present indicative).",
        },
    },
    {
        "card_id": "verb_imperative_chytai_2sg",
        "category": VerbCategory.IMPERATIVE_SYNTHETIC_ENDINGS,
        "cefr_level": "A1",
        "prompt_sentence": "Щодня вголос ___ хоча б кілька сторінок класичної літератури.",
        "blank_target": "читай",
        "correct_answer": "читай",
        "distractors": [
            {
                "text": "читаї",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING],
            },
            {
                "text": "читий",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING],
            },
            {
                "text": "читей",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Після голосного основа наказового способу закінчується на [j] і має нульове закінчення: «читай» (а не *читаї).",
            "en": "After a vowel, the imperative stem ends in /j/ with zero ending: 'chytai' (not *chytai).",
        },
    },
    {
        "card_id": "verb_imperative_stan_2sg",
        "category": VerbCategory.IMPERATIVE_SYNTHETIC_ENDINGS,
        "cefr_level": "A2",
        "prompt_sentence": "Будь ласка, спокійно ___ отут біля вікна і зачекай кілька хвилин.",
        "blank_target": "стань",
        "correct_answer": "стань",
        "distractors": [
            {
                "text": "станій",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING],
            },
            {
                "text": "станечко",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING],
            },
            {
                "text": "станіть",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Дієслово «стати» у наказовому способі має м'який кінцевий приголосний і нульове закінчення: «стань» (Правопис 2019 § 116).",
            "en": "Imperative of 'staty' ends in soft consonant with zero ending: 'stan' (Pravopys 2019 § 116).",
        },
    },
    {
        "card_id": "verb_imperative_vir_2pl",
        "category": VerbCategory.IMPERATIVE_SYNTHETIC_ENDINGS,
        "cefr_level": "A2",
        "prompt_sentence": "Ніколи не втрачайте надії і завжди щиро ___ у свої власні сили!",
        "blank_target": "вірте",
        "correct_answer": "вірте",
        "distractors": [
            {
                "text": "віріть",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING],
            },
            {
                "text": "віряйте",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "вірите",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Форма наказового способу від «вірити» має твердий кінцевий [р] і закінчення -те: «вірте» (а не *віріть чи дійсний час «вірите»).",
            "en": "Imperative of 'viryty' takes hard [r] + -te: 'virte' (not *virit or indicative 'viryte').",
        },
    },

    # =========================================================================
    # 10. IMPERATIVE_INCLUSIVE_1PL (Заклик до спільної дії: -мо / -імо) [§ 116]
    # =========================================================================
    {
        "card_id": "verb_imperative_1pl_khodimo",
        "category": VerbCategory.IMPERATIVE_INCLUSIVE_1PL,
        "cefr_level": "A1",
        "prompt_sentence": "Друзі, на вулиці чудова весняна погода, негайно ___ на прогулянку!",
        "blank_target": "ходімо",
        "correct_answer": "ходімо",
        "distractors": [
            {
                "text": "ходімте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
            {
                "text": "підемте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
            {
                "text": "ходимо",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Форма 1-ї особи множини наказового способу має нормативне закінчення -імо: «ходімо!» (форми *ходімте та *підемте є калькою з російської).",
            "en": "Standard 1st person plural imperative takes ending -imo: 'khodimo!' (not *khodimte or *pidemte).",
        },
    },
    {
        "card_id": "verb_imperative_1pl_robimo",
        "category": VerbCategory.IMPERATIVE_INCLUSIVE_1PL,
        "cefr_level": "A2",
        "prompt_sentence": "Час не чекає, друзі, тому дружно й завзято ___ цю справу разом!",
        "blank_target": "робімо",
        "correct_answer": "робімо",
        "distractors": [
            {
                "text": "робімте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
            {
                "text": "робимо",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
            {
                "text": "робитимемо",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Заклик до спільної дії в українській мові має закінчення -імо: «робімо!» (а не русифіковане *робімте).",
            "en": "The Ukrainian joint imperative form takes ending -imo: 'robimo!' (not *robimte).",
        },
    },
    {
        "card_id": "verb_imperative_1pl_chytaimo",
        "category": VerbCategory.IMPERATIVE_INCLUSIVE_1PL,
        "cefr_level": "A1",
        "prompt_sentence": "Відкрийте підручники на десятій сторінці і гуртом ___ цей вірш!",
        "blank_target": "читаймо",
        "correct_answer": "читаймо",
        "distractors": [
            {
                "text": "читаємте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
            {
                "text": "читаємо",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
            {
                "text": "читаймоте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Після голосного [j] у наказовому способі 1-ї особи множини виступає закінчення -мо: «читаймо!» (а не *читаємте).",
            "en": "After /j/, 1pl imperative takes ending -mo: 'chytaimo!' (not *chytaiemte).",
        },
    },
    {
        "card_id": "verb_imperative_1pl_pratsiuiemo",
        "category": VerbCategory.IMPERATIVE_INCLUSIVE_1PL,
        "cefr_level": "A2",
        "prompt_sentence": "Не гаймо жодної дорогоцінної хвилини, колеги, а згуртовано ___!",
        "blank_target": "працюймо",
        "correct_answer": "працюймо",
        "distractors": [
            {
                "text": "працюємте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
            {
                "text": "працюємо",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
            {
                "text": "працюватимемо",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Нормативна форма наказового способу 1-ї особи множини: «працюймо!» (форма «працюємо» позначає дійсний спосіб, а *працюємте — русизм).",
            "en": "Standard 1pl imperative is 'pratsiuimo!' ('pratsyuiemo' is indicative, '*pratsyuiemte' is a Russianism).",
        },
    },
    {
        "card_id": "verb_imperative_1pl_napyshimo",
        "category": VerbCategory.IMPERATIVE_INCLUSIVE_1PL,
        "cefr_level": "A2",
        "prompt_sentence": "Шановні одногрупники, щиро та відкрито ___ колективне звернення!",
        "blank_target": "напишімо",
        "correct_answer": "напишімо",
        "distractors": [
            {
                "text": "напишімте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
            {
                "text": "напишемо",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_INDICATIVE_CONFUSION],
            },
            {
                "text": "напишемте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Заклик до спільної дії від дієслова «написати» має закінчення -імо: «напишімо!» (а не *напишімте чи *напишемо).",
            "en": "Joint encouragement from 'napysaty' takes ending -imo: 'napyshimo!' (not *napyshimte).",
        },
    },

    # =========================================================================
    # 11. IMPERATIVE_ANTI_CALQUE_DAVAI (Усунення кальок «давай(те) робити») [§ 116]
    # =========================================================================
    {
        "card_id": "verb_anti_calque_davai_zrobymo",
        "category": VerbCategory.IMPERATIVE_ANTI_CALQUE_DAVAI,
        "cefr_level": "A2",
        "prompt_sentence": "Друзі, замість суржикового «давайте зробимо», правильно сказати: «___ це негайно!»",
        "blank_target": "зробімо",
        "correct_answer": "зробімо",
        "distractors": [
            {
                "text": "давайте зробимо",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "давай робити",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "зробімте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Конструкції зі словами «давай / давайте» є калькою з російської. Питома українська форма наказового способу: «зробімо!».",
            "en": "Constructions with 'davai / davaite' are Russian calques. Native Ukrainian imperative is 'zrobimo!'.",
        },
    },
    {
        "card_id": "verb_anti_calque_davai_pochnemo",
        "category": VerbCategory.IMPERATIVE_ANTI_CALQUE_DAVAI,
        "cefr_level": "A2",
        "prompt_sentence": "Усі готові до обговорення, тому без зайвих слів ___ нашу зустріч!",
        "blank_target": "почнімо",
        "correct_answer": "почнімо",
        "distractors": [
            {
                "text": "давайте почнемо",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "давай починати",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "почнімте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Замість кальки «давайте почнемо» нормативна українська мова вимагає синтетичну форму: «почнімо!».",
            "en": "Instead of calqued 'davaite pochnemo', standard Ukrainian strictly uses 'pochnimo!'.",
        },
    },
    {
        "card_id": "verb_anti_calque_davai_pohovorymo",
        "category": VerbCategory.IMPERATIVE_ANTI_CALQUE_DAVAI,
        "cefr_level": "B1",
        "prompt_sentence": "Не варто відкладати розв'язання проблеми, краще щиро й відверто ___ про все.",
        "blank_target": "поговорімо",
        "correct_answer": "поговорімо",
        "distractors": [
            {
                "text": "давай поговоримо",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "давайте балакати",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "поговорімте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Українська літературна норма не вживає «давай поговоримо», а послуговується формою «поговорімо!».",
            "en": "Ukrainian literary standard rejects 'davai pohovorymo' in favor of 'pohovorimo!'.",
        },
    },
    {
        "card_id": "verb_anti_calque_davai_spivaimo",
        "category": VerbCategory.IMPERATIVE_ANTI_CALQUE_DAVAI,
        "cefr_level": "A2",
        "prompt_sentence": "Свято в розпалі, тому разом і дзвінко ___ цю прекрасну народну пісню!",
        "blank_target": "заспіваймо",
        "correct_answer": "заспіваймо",
        "distractors": [
            {
                "text": "давайте заспіваємо",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "давай співати",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "заспіваємте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Форма заклику до співу: «заспіваймо!» (сполучення «давайте заспіваємо» — ненормативна калька).",
            "en": "The correct joint imperative is 'zaspivaimo!' (avoiding Russian calque 'davaite zaspivaemo').",
        },
    },
    {
        "card_id": "verb_anti_calque_davai_zhymo",
        "category": VerbCategory.IMPERATIVE_ANTI_CALQUE_DAVAI,
        "cefr_level": "B1",
        "prompt_sentence": "Замість постійних сварок і суперечок, ___ дружно та поважаймо одне одного!",
        "blank_target": "живімо",
        "correct_answer": "живімо",
        "distractors": [
            {
                "text": "давайте жити",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "давай будемо жити",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_DAVAI_IMPERATIVE],
            },
            {
                "text": "живімте",
                "interference_type": VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 116",
        "rule_summary": {
            "ua": "Синтетична нормативна форма наказового способу: «живімо!» (а не калька «давайте жити»).",
            "en": "Standard synthetic imperative: 'zhyvimo!' (not calqued 'davaite zhyty').",
        },
    },

    # =========================================================================
    # 12. PARTICIPLE_PASSIVE_FORMATION (-ний / -тий) [§ 119]
    # =========================================================================
    {
        "card_id": "verb_participle_napysanyi",
        "category": VerbCategory.PARTICIPLE_PASSIVE_FORMATION,
        "cefr_level": "A2",
        "prompt_sentence": "Цей змістовний і глибокий лист був щиро ___ від щирого серця.",
        "blank_target": "написаний",
        "correct_answer": "написаний",
        "distractors": [
            {
                "text": "написатий",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "напишений",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "написавший",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Пасивний дієприкметник від дієслова «написати» твориться за допомогою суфікса -ний: «написаний» (Правопис 2019 § 119).",
            "en": "Passive participle of 'napysaty' is formed with suffix -nyi: 'napysanyi' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_participle_rozbytyi",
        "category": VerbCategory.PARTICIPLE_PASSIVE_FORMATION,
        "cefr_level": "A2",
        "prompt_sentence": "На бруківці блищало на сонці випадково ___ кришталеве дзеркальце.",
        "blank_target": "розбите",
        "correct_answer": "розбите",
        "distractors": [
            {
                "text": "розбине",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "розбитене",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "розбивше",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Від односкладових дієслівних основ на голосний пасивні дієприкметники творяться суфіксом -тий: «розбитий» / «розбите» (Правопис 2019 § 119).",
            "en": "Monosyllabic vowel stems form passive participles with suffix -tyi: 'rozbytyi' / 'rozbyte' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_participle_vidkrytyi",
        "category": VerbCategory.PARTICIPLE_PASSIVE_FORMATION,
        "cefr_level": "A2",
        "prompt_sentence": "Усі присутні звернули увагу на навстіж ___ вікно на другому поверсі.",
        "blank_target": "відкрите",
        "correct_answer": "відкрите",
        "distractors": [
            {
                "text": "відкрине",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "відкривше",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "відкритеє",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Дієслово «відкрити» творить пасивний дієприкметник за допомогою суфікса -тий: «відкритий» / «відкрите» (Правопис 2019 § 119).",
            "en": "Passive participle of 'vidkryty' uses suffix -tyi: 'vidkrytyi' / 'vidkryte' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_participle_zroblenyi",
        "category": VerbCategory.PARTICIPLE_PASSIVE_FORMATION,
        "cefr_level": "A2",
        "prompt_sentence": "Цей стильний дерев'яний стіл був майстерно ___ народним умільцем.",
        "blank_target": "зроблений",
        "correct_answer": "зроблений",
        "distractors": [
            {
                "text": "зробний",
                "interference_type": VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L],
            },
            {
                "text": "зроблетий",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "зробивший",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "При творенні пасивного дієприкметника від «зробити» після губного [б] виступає вставний [л'] + суфікс -ен-: «зроблений» (Правопис 2019 § 119).",
            "en": "Passive participle from 'zrobyty' requires epenthetic [l'] + -en-: 'zroblenyi' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_participle_zshytyi",
        "category": VerbCategory.PARTICIPLE_PASSIVE_FORMATION,
        "cefr_level": "B1",
        "prompt_sentence": "Цей розкішний традиційний костюм був вручну ___ із міцного полотна.",
        "blank_target": "зшитий",
        "correct_answer": "зшитий",
        "distractors": [
            {
                "text": "зшиний",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "зшитений",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
            {
                "text": "зшивший",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Пасивний дієприкметник від «зшити» твориться за допомогою суфікса -тий: «зшитий» (Правопис 2019 § 119).",
            "en": "Passive participle of 'zshyty' uses suffix -tyi: 'zshytyi' (Pravopys 2019 § 119).",
        },
    },

    # =========================================================================
    # 13. PARTICIPLE_ANTI_CALQUE_ACTIVE (Усунення активних дієприкметників) [§ 119]
    # =========================================================================
    {
        "card_id": "verb_anti_calque_okhochi",
        "category": VerbCategory.PARTICIPLE_ANTI_CALQUE_ACTIVE,
        "cefr_level": "B1",
        "prompt_sentence": "Усі ___ взяти активну участь в олімпіаді мають зареєструватися до кінця тижня.",
        "blank_target": "охочі",
        "correct_answer": "охочі",
        "distractors": [
            {
                "text": "бажаючі",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "побажаючі",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "бажаючими",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Форма *бажаючі є типовим русизмом. В українській мові слід вживати прикметник «охочі» або конструкцію «ті, хто бажає» (Правопис 2019 § 119).",
            "en": "The form *bazhaiuchi is a Russian calque; use adjective 'okhochi' or clause 'ti, khto bazhaie' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_anti_calque_chynnyi",
        "category": VerbCategory.PARTICIPLE_ANTI_CALQUE_ACTIVE,
        "cefr_level": "B1",
        "prompt_sentence": "Згідно з нормами українського права, на території держави діє лише ___ закон.",
        "blank_target": "чинний",
        "correct_answer": "чинний",
        "distractors": [
            {
                "text": "діючий",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "діющій",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "діющого",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Словосполучення *діючий закон є калькою. Нормативна форма сучасної мови: «чинний закон» (Правопис 2019 § 119).",
            "en": "The phrase *diiuchyi zakon is a calque; standard Ukrainian uses 'chynnyi zakon' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_anti_calque_pochatkivets",
        "category": VerbCategory.PARTICIPLE_ANTI_CALQUE_ACTIVE,
        "cefr_level": "B1",
        "prompt_sentence": "Цей молодий талановитий ___ опублікував свою першу чудову збірку віршів.",
        "blank_target": "початківець",
        "correct_answer": "початківець",
        "distractors": [
            {
                "text": "початкуючий автор",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "початкуючий",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "початкований",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Активний дієприкметник *початкуючий є ненормативним. Правильно вживати іменник: «початківець» або «автор-початківець» (Правопис 2019 § 119).",
            "en": "The active participle *pochatkuiuchyi is non-standard; use noun 'pochatkivets' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_anti_calque_vykonuvach",
        "category": VerbCategory.PARTICIPLE_ANTI_CALQUE_ACTIVE,
        "cefr_level": "B2",
        "prompt_sentence": "Офіційний наказ підписав тимчасовий ___ обов'язків генерального директора.",
        "blank_target": "виконувач",
        "correct_answer": "виконувач",
        "distractors": [
            {
                "text": "виконуючий",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "виконуючийся",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "виконуючим",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "В офіційно-діловому стилі не вживають *виконуючий обов'язки (русизм). Нормативний український відповідник: «виконувач обов'язків» (т.в.о.) (Правопис 2019 § 119).",
            "en": "In official style, avoid calqued *vykonuiuchyi obov'iazky; use 'vykonuvach obov'iazkiv' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_anti_calque_panivnyi",
        "category": VerbCategory.PARTICIPLE_ANTI_CALQUE_ACTIVE,
        "cefr_level": "B2",
        "prompt_sentence": "У тогочасному європейському суспільстві це була загальновизнана й ___ ідея.",
        "blank_target": "панівна",
        "correct_answer": "панівна",
        "distractors": [
            {
                "text": "пануюча",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "пануючая",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
            {
                "text": "панована",
                "interference_type": VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Замість невластивої форми *пануюча українська мова послуговується нормативним прикметником: «панівна» (панівний настрій, панівна ідея) (Правопис 2019 § 119).",
            "en": "Avoid alien *panuiucha; use standard adjective 'panivna' (Pravopys 2019 § 119).",
        },
    },

    # =========================================================================
    # 14. PARTICIPLE_IMPERSONAL_NO_TO (Безособові форми на -но / -то) [§ 119]
    # =========================================================================
    {
        "card_id": "verb_impersonal_vykonano",
        "category": VerbCategory.PARTICIPLE_IMPERSONAL_NO_TO,
        "cefr_level": "A2",
        "prompt_sentence": "Усі заплановані ремонтні роботи в школі було успішно й вчасно ___.",
        "blank_target": "виконано",
        "correct_answer": "виконано",
        "distractors": [
            {
                "text": "виконані",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "виконані були",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "виконане",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "У безособових реченнях із дієслівною зв'язкою «було» вживається незмінювана предикативна форма на -но: «було виконано» (а не узгоджений дієприкметник *були виконані) (Правопис 2019 § 119).",
            "en": "Impersonal predicates with 'bulo' strictly take invariant -no form: 'bulo vykonano' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_impersonal_pryiniato",
        "category": VerbCategory.PARTICIPLE_IMPERSONAL_NO_TO,
        "cefr_level": "B1",
        "prompt_sentence": "Верховною Радою України одноголосно ___ новий демократичний закон.",
        "blank_target": "прийнято",
        "correct_answer": "прийнято",
        "distractors": [
            {
                "text": "прийнятий",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "прийнятого",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "прийнятим",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Безособова присудкова конструкція із прямим додатком у знахідному відмінку вимагає форми на -то: «прийнято новий закон» (Правопис 2019 § 119).",
            "en": "Impersonal verbal predicate with direct accusative object takes -to form: 'pryiniato novyi zakon' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_impersonal_pidpysano",
        "category": VerbCategory.PARTICIPLE_IMPERSONAL_NO_TO,
        "cefr_level": "B1",
        "prompt_sentence": "Міжнародну безпекову угоду між державами було урочисто ___ в столиці.",
        "blank_target": "підписано",
        "correct_answer": "підписано",
        "distractors": [
            {
                "text": "підписана",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "підписану",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "підписаної",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Незмінювана дієслівна форма на -но утворює нормативний безособовий присудок: «було підписано» (Правопис 2019 § 119).",
            "en": "Invariant verbal form in -no creates standard impersonal predicate: 'bulo pidpysano' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_impersonal_vidchyneno",
        "category": VerbCategory.PARTICIPLE_IMPERSONAL_NO_TO,
        "cefr_level": "A2",
        "prompt_sentence": "Вранці для перших відвідувачів виставки було гостинно ___ масивні дубові двері.",
        "blank_target": "відчинено",
        "correct_answer": "відчинено",
        "distractors": [
            {
                "text": "відчинені",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "відчинена",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "відчинене",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Безособова форма на -но керує знахідним відмінком прямого додатка: «було відчинено двері» (Правопис 2019 § 119).",
            "en": "Impersonal form in -no governs accusative object: 'bulo vidchyneno dveri' (Pravopys 2019 § 119).",
        },
    },
    {
        "card_id": "verb_impersonal_rozkryto",
        "category": VerbCategory.PARTICIPLE_IMPERSONAL_NO_TO,
        "cefr_level": "B2",
        "prompt_sentence": "У цій глибокій монографії блискуче й вичерпно ___ складну історичну проблему.",
        "blank_target": "розкрито",
        "correct_answer": "розкрито",
        "distractors": [
            {
                "text": "розкрита",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "розкритий",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "розкриту",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
        ],
        "pravopys_section": "Правопис 2019 § 119",
        "rule_summary": {
            "ua": "Безособова дієслівна форма на -то утворює динамічний присудок: «розкрито проблему» (Правопис 2019 § 119).",
            "en": "Impersonal form in -to forms dynamic predicate: 'rozkryto problemu' (Pravopys 2019 § 119).",
        },
    },

    # =========================================================================
    # 15. GERUND_FORMATION_ASPECT (Дієприслівник: недок. -учи/-ачи vs док. -вши/-ши) [§ 120]
    # =========================================================================
    {
        "card_id": "verb_gerund_chytayuchy",
        "category": VerbCategory.GERUND_FORMATION_ASPECT,
        "cefr_level": "A2",
        "prompt_sentence": "Сидячи в затишному кріслі й повільно ___ цікаву повість, я відпочиваю.",
        "blank_target": "читаючи",
        "correct_answer": "читаючи",
        "distractors": [
            {
                "text": "читавши",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
            {
                "text": "читаячи",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
            {
                "text": "прочитаючи",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
        ],
        "pravopys_section": "Правопис 2019 § 120",
        "rule_summary": {
            "ua": "Для позначення додаткової одночасної дії дієслово I дієвідміни недоконаного виду «читати» утворює дієприслівник на -ючи: «читаючи» (Правопис 2019 § 120).",
            "en": "For simultaneous imperfective action, Class I verb 'chytaty' forms gerund with -iuchy: 'chytaiuchy' (Pravopys 2019 § 120).",
        },
    },
    {
        "card_id": "verb_gerund_sydiachy",
        "category": VerbCategory.GERUND_FORMATION_ASPECT,
        "cefr_level": "A2",
        "prompt_sentence": "Студенти уважно слухали лекцію викладача, тихо ___ за своїми партами.",
        "blank_target": "сидячи",
        "correct_answer": "сидячи",
        "distractors": [
            {
                "text": "сидучи",
                "interference_type": VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I],
            },
            {
                "text": "сидівши",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
            {
                "text": "сидячих",
                "interference_type": VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.RUSSIAN_CALQUE_ACTIVE_PARTICIPLE],
            },
        ],
        "pravopys_section": "Правопис 2019 § 120",
        "rule_summary": {
            "ua": "Дієслово II дієвідміни «сидіти» (сидять) утворює дієприслівник недоконаного виду за допомогою суфікса -ячи: «сидячи» (Правопис 2019 § 120).",
            "en": "Class II verb 'sydity' (sydiat) forms imperfective gerund with -iachy: 'sydiachy' (Pravopys 2019 § 120).",
        },
    },
    {
        "card_id": "verb_gerund_prochytavshy",
        "category": VerbCategory.GERUND_FORMATION_ASPECT,
        "cefr_level": "A2",
        "prompt_sentence": "Уважно ___ останню сторінку контракту, юрист поставив свій підпис.",
        "blank_target": "прочитавши",
        "correct_answer": "прочитавши",
        "distractors": [
            {
                "text": "прочитаючи",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
            {
                "text": "прочитано",
                "interference_type": VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_IMPERSONAL_FORMS_AGREEMENT],
            },
            {
                "text": "прочитавшися",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
        ],
        "pravopys_section": "Правопис 2019 § 120",
        "rule_summary": {
            "ua": "Для позначення попередньої завершеної дії дієслово доконаного виду «прочитати» утворює дієприслівник на -вши: «прочитавши» (Правопис 2019 § 120).",
            "en": "Prior completed action from perfective 'prochytaty' forms gerund with -vshy: 'prochytaffshy' (Pravopys 2019 § 120).",
        },
    },
    {
        "card_id": "verb_gerund_prynisshy",
        "category": VerbCategory.GERUND_FORMATION_ASPECT,
        "cefr_level": "B1",
        "prompt_sentence": "Швидко ___ свіжі квіти до кімнати, дівчина одразу поставила їх у вазу.",
        "blank_target": "принісши",
        "correct_answer": "принісши",
        "distractors": [
            {
                "text": "принесши",
                "interference_type": VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I],
            },
            {
                "text": "приносячи",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
            {
                "text": "принісшися",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
        ],
        "pravopys_section": "Правопис 2019 § 120",
        "rule_summary": {
            "ua": "Дієприслівник доконаного виду від дієслова на приголосний утворюється суфіксом -ши з чергуванням голосних: «принісши» (Правопис 2019 § 120).",
            "en": "Perfective gerund from consonant stem takes suffix -shy with root alternation: 'prynisshy' (Pravopys 2019 § 120).",
        },
    },
    {
        "card_id": "verb_gerund_lihshy",
        "category": VerbCategory.GERUND_FORMATION_ASPECT,
        "cefr_level": "B1",
        "prompt_sentence": "Зручно ___ на м'яку траву під тінню дерева, мандрівник одразу заснув.",
        "blank_target": "лігши",
        "correct_answer": "лігши",
        "distractors": [
            {
                "text": "лягнувши",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
            {
                "text": "лягши",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": {
                    "ua": "У дієприслівнику доконаного виду від «лягти» у закритому складі відбувається чергування кореневого [а] (я) на [і]: «лігши», а не «*лягши» (Правопис 2019 § 120).",
                    "en": "In the perfective gerund of 'liahty', the closed root syllable alternates [a] (ia) to [i]: 'lihshy', not '*liahshy' (Pravopys 2019 § 120).",
                },
            },
            {
                "text": "лігшися",
                "interference_type": VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX,
                "explanation": INTERFERENCE_EXPLANATIONS[VerbInterferenceType.FALSE_GERUND_ASPECT_SUFFIX],
            },
        ],
        "pravopys_section": "Правопис 2019 § 120",
        "rule_summary": {
            "ua": "Дієприслівник доконаного виду від «лягти» має форму з суфіксом -ши від основи минулого часу: «лігши» (Правопис 2019 § 120).",
            "en": "Perfective gerund from 'liahty' takes suffix -shy on the past stem: 'lihshy' (Pravopys 2019 § 120).",
        },
    },
]


def validate_verb_card(card: VerbCard) -> None:
    """Validate card integrity: zero collisions, valid distractor count, blank target in prompt."""
    if len(card.distractors) != 3:
        raise ValueError(
            f"Card {card.card_id} must have exactly 3 distractors, got {len(card.distractors)}"
        )
    opt_texts = [card.correct_answer.strip()] + [d.text.strip() for d in card.distractors]
    if len(set(opt_texts)) != 4:
        raise ValueError(
            f"Card {card.card_id} has collision or duplicate options: {opt_texts}"
        )
    if "___" not in card.prompt_sentence:
        raise ValueError(
            f"Card {card.card_id} prompt missing blank indicator '___': {card.prompt_sentence}"
        )
    for dist in card.distractors:
        if dist.text.strip() == card.correct_answer.strip():
            raise ValueError(
                f"Card {card.card_id} distractor matches correct answer: '{dist.text}'"
            )
        if not dist.explanation.get("ua") or not dist.explanation.get("en"):
            raise ValueError(
                f"Card {card.card_id} distractor '{dist.text}' missing bilingual explanation"
            )


def build_canonical_verb_cards() -> list[VerbCard]:
    """Instantiate and validate all canonical VerbCards."""
    cards: list[VerbCard] = []
    for raw in CANONICAL_VERB_CARDS:
        distractors = [
            VerbDistractor(
                text=d["text"],
                interference_type=d["interference_type"],
                explanation=d["explanation"],
            )
            for d in raw["distractors"]
        ]
        card = VerbCard(
            card_id=raw["card_id"],
            category=raw["category"],
            cefr_level=raw["cefr_level"],
            prompt_sentence=raw["prompt_sentence"],
            blank_target=raw["blank_target"],
            correct_answer=raw["correct_answer"],
            distractors=distractors,
            pravopys_section=raw["pravopys_section"],
            rule_summary=raw["rule_summary"],
        )
        validate_verb_card(card)
        cards.append(card)
    return cards


def export_verb_mechanics_deck(
    cards: list[VerbCard], out_path: Path | None = None
) -> dict[str, Any]:
    """Export cards to JSON payload matching the contract."""
    payload = {
        "schema_version": "1.0",
        "card_count": len(cards),
        "cards": [c.to_dict() for c in cards],
    }
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return payload


def find_vesum_db(specified: Path | None = None) -> Path:
    """Finds vesum.db checking specified path, local tree, or primary checkout."""
    if specified and specified.exists():
        return specified
    candidates = [
        PROJECT_ROOT / "data" / "vesum.db",
        PROJECT_ROOT.parent.parent.parent / "data" / "vesum.db",
        Path("/home/ops/learn-ukrainian/data/vesum.db"),
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 1000:
            return c
    return specified or (PROJECT_ROOT / "data" / "vesum.db")


def verify_deck_with_vesum(
    cards: list[VerbCard], db_path: Path | None = None
) -> dict[str, Any]:
    """Verify target words in cards against VESUM database if available."""
    resolved_path = find_vesum_db(db_path)
    if not resolved_path.exists() or resolved_path.stat().st_size < 1_000_000:
        return {
            "verified": None,
            "status": "skipped",
            "reason": f"VESUM database not found or incomplete at {resolved_path}",
            "checked_word_count": 0,
        }

    conn = sqlite3.connect(str(resolved_path))
    cursor = conn.cursor()
    missing: list[dict[str, str]] = []
    checked = 0

    for card in cards:
        target = card.correct_answer.strip()
        words = target.split()
        for word in words:
            clean_word = word.strip(".,;:!?«»\"'")
            if not clean_word:
                continue
            checked += 1
            cursor.execute("SELECT 1 FROM forms_all WHERE word_form = ? LIMIT 1", (clean_word,))
            if not cursor.fetchone():
                cursor.execute("SELECT 1 FROM forms WHERE word_form = ? LIMIT 1", (clean_word,))
                if not cursor.fetchone():
                    missing.append({"card_id": card.card_id, "word": clean_word, "target_answer": target})

    conn.close()
    return {
        "verified": len(missing) == 0,
        "status": "passed" if len(missing) == 0 else "failed",
        "checked_word_count": checked,
        "missing_forms": missing,
    }


def verify_distractors_with_vesum(
    cards: list[VerbCard], db_path: Path | None = None
) -> dict[str, Any]:
    """Ensure morphological/phonological corruption distractors are NOT valid standard forms in VESUM."""
    resolved_path = find_vesum_db(db_path)
    if not resolved_path.exists() or resolved_path.stat().st_size < 1_000_000:
        return {
            "verified": None,
            "status": "skipped",
            "reason": f"VESUM database not found or incomplete at {resolved_path}",
            "checked_distractor_count": 0,
        }

    corruption_types = {
        VerbInterferenceType.FALSE_CONJUGATION_CLASS_I_FOR_II,
        VerbInterferenceType.FALSE_CONJUGATION_CLASS_II_FOR_I,
        VerbInterferenceType.FALSE_LABIAL_MISSING_EPENTHESIS_L,
        VerbInterferenceType.FALSE_DENTAL_MISSING_MUTATION_1SG,
        VerbInterferenceType.FALSE_STEM_MUTATION_CLASS_I,
        VerbInterferenceType.FALSE_IMPERATIVE_MISSING_Y_ENDING,
        VerbInterferenceType.FALSE_IMPERATIVE_EXCESSIVE_Y_ENDING,
        VerbInterferenceType.FALSE_IMPERATIVE_1PL_RUSSIAN_TE,
        VerbInterferenceType.FALSE_PARTICIPLE_SUFFIX_NYI_TYI,
        VerbInterferenceType.FALSE_ASPECT_IMPERFECTIVATION_ABLAUT,
    }

    conn = sqlite3.connect(str(resolved_path))
    cursor = conn.cursor()
    invalid_distractors: list[dict[str, Any]] = []
    checked = 0

    for card in cards:
        for dist in card.distractors:
            if dist.interference_type in corruption_types:
                clean_text = dist.text.strip().replace(" би", "").replace(" ся", "").strip(".,;:!?«»\"'")
                checked += 1
                cursor.execute(
                    "SELECT lemma, pos, tags FROM forms_all WHERE word_form = ?",
                    (clean_text,),
                )
                rows = cursor.fetchall()
                if not rows:
                    cursor.execute(
                        "SELECT lemma, pos, tags FROM forms WHERE word_form = ?",
                        (clean_text,),
                    )
                    rows = cursor.fetchall()

                # A distractor is invalid if it matches a standard verb, gerund, or participle form in VESUM without non-standard tags
                standard_verb_rows = [
                    r
                    for r in rows
                    if (
                        r[1].startswith("verb")
                        or r[1] == "advp"
                        or (r[1] == "adj" and "adjp" in r[2])
                    )
                    and ":bad" not in r[2]
                    and ":alt" not in r[2]
                    and ":subst" not in r[2]
                    and ":arch" not in r[2]
                    and ":dial" not in r[2]
                ]
                if standard_verb_rows:
                    invalid_distractors.append(
                        {
                            "card_id": card.card_id,
                            "distractor": dist.text,
                            "interference_type": dist.interference_type.value,
                            "matching_vesum_rows": standard_verb_rows,
                        }
                    )

    conn.close()
    return {
        "verified": len(invalid_distractors) == 0,
        "status": "passed" if len(invalid_distractors) == 0 else "failed",
        "checked_distractor_count": checked,
        "invalid_distractors": invalid_distractors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ukrainian Verb Deep Mechanics Practice Engine")
    parser.add_argument(
        "--export",
        type=Path,
        default=PROJECT_ROOT / "data" / "practice" / "verb_mechanics_deck.json",
        help="Path to export compiled JSON practice deck",
    )
    parser.add_argument(
        "--verify-vesum",
        action="store_true",
        help="Verify inflected targets against VESUM sqlite database",
    )
    args = parser.parse_args()

    cards = build_canonical_verb_cards()
    print(f"Validated {len(cards)} canonical verb practice cards across {len(VerbCategory)} categories.")

    export_verb_mechanics_deck(cards, args.export)
    print(f"Exported deck to {args.export}")

    if args.verify_vesum:
        report = verify_deck_with_vesum(cards)
        print(f"VESUM verification: {report}")
        dist_report = verify_distractors_with_vesum(cards)
        print(f"VESUM distractor verification: {dist_report}")
        if report.get("verified") is False or dist_report.get("verified") is False:
            print("ERROR: VESUM verification failed!", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
