"""Ukrainian Adjective Deep Mechanics Practice Engine (Прикметник).

Implements Ukrainian Pravopys 2019:
  - Part I, § 22: Чергування приголосних при творенні слів (г, ж, з -> -зьк-, к, ч, ц -> -цьк-, х, ш, с -> -ськ-; г->ж, к->ч, х->ш).
  - Part III, §§ 106–114: Морфологія — Прикметник (офіційне видання НАН України / Інститут мовознавства):
    * § 106: Поділ на тверду та м'яку групи.
    * § 107: Творення присвійних прикметників (-ів/-ова/-еве, -ин/-ина/-єве; чергування перед -ин).
    * § 108: Відмінювання прикметників твердої та м'якої груп (-ого/-ього, -ому/-ьому, орудний -ім).
    * § 110: Творення вищого ступеня (п. 1 а: суфікси -ш-/-іш- та випадання -к-/-ок-; п. 1 б: чергування -жч-, -щ-; п. 1 в: суплетивні; п. 2: складена форма).
    * § 111: Творення найвищого ступеня (префікс най-, підсилювальні якнай-, щонай-; складена форма).

Rules covered:
  1. Degrees of Comparison (Ступені порівняння прикметників) [Правопис 2019 §§ 110–114]:
     - Comparative (Вищий ступінь):
       * Simple synthetic form with -ш- / -іш- and morphophonemic mutations:
         - г, ж, з + -ш- -> -жч- (дорогий -> дорожчий, дужий -> дужчий, низький -> нижчий,
           вузький -> вужчий, близький -> ближчий, важкий -> важчий).
         - к, с, ст + -ш- -> -щ- (високий -> вищий, товстий -> товщий, кращий).
         - Suffix dropping: суфікси -к-, -ок- випадають перед -ш- (швидкий -> швидший,
           широкий -> ширший, глибокий -> глибший, короткий -> коротший).
         - Regular suffix -іш- for cluster/hard stems (новий -> новіший, теплий -> тепліший,
           розумний -> розумніший, гарний -> гарніший, сильний -> сильніший).
       * Suppletive stems: великий -> більший, малий -> менший, поганий -> гірший,
         добрий/хороший -> кращий / ліпший.
       * Compound analytic form: більш / менш + base adjective (більш зручний, менш доступний,
         більш досвідчений, менш складний). Anti-error: *більш зручніший (double comparative).
     - Superlative (Найвищий ступінь):
       * Simple synthetic form: prefix най- + comparative (найкращий, найвищий, найдорожчий,
         найбільший, найменший, найважливіший). Anti-calque: *самий кращий, *самий великий.
       * Emphatic prefixes: якнай-, щонай- (якнайшвидший, щонайкращий, якнайбільший).
       * Compound analytic form: найбільш / найменш + base adjective (найбільш важливий,
         найменш вдалий).
     - Uncomparable Adjectives:
       * Absolute qualities, materials, and relational categories that cannot form degrees:
         дерев'яний, босий, сліпий, вчорашній, залізний.

  2. Declension Groups: Hard vs Soft (Тверда та м'яка групи прикметників) [Правопис 2019 §§ 106–109]:
     - Hard group: -ий, -ого, -ому, -им, -ому/-ім (новий, нового, новому, новим).
     - Soft group: -ій, -ього, -ьому, -ім, -ьому/-ім (синій, синього, синьому, синім).
     - High-error focus: masculine/neuter soft instrumental singular ending is strictly -ім
       (синім, літнім, осіннім, раннім, вечірнім, давнім, крайнім), NOT *-им* (*синим*, *літним*).
     - Soft Genitive/Dative: -ього / -ьому (синього, літнього, давнього, безкрайого).

  3. Possessive Adjectives & Morphophonemic Suffixation [Правопис 2019 §§ 22, 107]:
     - Suffix -ів (-ова, -ове, -еве, -єве) from II declension masculine nouns
       (батьків, Шевченків, Франків, братів; Василів -> Василева; Сергіїв -> Сергієве).
     - Suffix -ин (-ина, -ине) from I declension nouns with historical consonant alternations:
       * г -> ж: Ольга -> Ольжин.
       * к -> ч: дочка -> доччин, тітка -> тітчин, курка -> курчин.
       * х -> ш: Солоха -> Солошин, мачуха -> мачушин, свекруха -> свекрушин.
     - Derivational suffixes -ськ-, -цьк-, -зьк- (§ 22):
       * г, ж, з + -ськ- -> -зьк- (Прага -> празький, Запоріжжя -> запорізький).
       * к, ч, ц + -ськ- -> -цьк- (козак -> козацький, ткач -> ткацький).
       * х, ш, с + -ськ- -> -ськ- (чех -> чеський, товариш -> товариський).

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


class AdjectiveCategory(StrEnum):
    """Categories of adjective deep mechanics practice."""

    COMP_SYNTHETIC_MUTATION_ZHCH = "comp_synthetic_mutation_zhch"
    COMP_SYNTHETIC_MUTATION_SHCH = "comp_synthetic_mutation_shch"
    COMP_SYNTHETIC_SH_DROPPING_K = "comp_synthetic_sh_dropping_k"
    COMP_SYNTHETIC_ISH = "comp_synthetic_ish"
    COMP_SUPPLETIVE = "comp_suppletive"
    COMP_ANALYTIC_FORMATION = "comp_analytic_formation"
    SUPER_SYNTHETIC_PREFIX = "super_synthetic_prefix"
    SUPER_EMPHATIC_PREFIX = "super_emphatic_prefix"
    DECL_SOFT_INSTRUMENTAL_IM = "decl_soft_instrumental_im"
    DECL_SOFT_GENITIVE_DATIVE = "decl_soft_genitive_dative"
    POSSESSIVE_IV_DECLENSION = "possessive_iv_declension"
    POSSESSIVE_YN_MUTATION = "possessive_yn_mutation"
    SUFFIX_DERIVATION_MUTATION = "suffix_derivation_mutation"
    ANTI_CALQUE_UNCOMPARABLE = "anti_calque_uncomparable"


class AdjectiveInterferenceType(StrEnum):
    """Taxonomy of morphological, phonological, and syntactic adjective misconceptions."""

    FALSE_SYNTHETIC_MISSING_MUTATION = "false_synthetic_missing_mutation"
    FALSE_SH_DROPPING_K_MISSING_DROP = "false_sh_dropping_k_missing_drop"
    FALSE_COMPARATIVE_ISH_FOR_SH = "false_comparative_ish_for_sh"
    FALSE_COMPARATIVE_SH_FOR_ISH = "false_comparative_sh_for_ish"
    FALSE_SUPPLETIVE_REGULARIZED = "false_suppletive_regularized"
    FALSE_DOUBLE_COMPARATIVE = "false_double_comparative"
    RUSSIAN_CALQUE_SAMYI = "russian_calque_samyi"
    FALSE_SUPERLATIVE_PREFIX_SEPARATED = "false_superlative_prefix_separated"
    FALSE_SUPERLATIVE_ANALYTIC_DOUBLE = "false_superlative_analytic_double"
    FALSE_SOFT_INSTRUMENTAL_YM = "false_soft_instrumental_ym"
    FALSE_SOFT_GENITIVE_HARD_ENDING = "false_soft_genitive_hard_ending"
    FALSE_SOFT_DATIVE_HARD_ENDING = "false_soft_dative_hard_ending"
    FALSE_POSSESSIVE_MISSING_MUTATION = "false_possessive_missing_mutation"
    FALSE_POSSESSIVE_IV_SUFFIX_VOWEL = "false_possessive_iv_suffix_vowel"
    FALSE_DERIVATION_MISSING_MUTATION = "false_derivation_missing_mutation"
    FALSE_COMPARISON_OF_UNCOMPARABLE = "false_comparison_of_uncomparable"
    FALSE_RELATIONAL_FOR_POSSESSIVE = "false_relational_for_possessive"


INTERFERENCE_EXPLANATIONS: dict[AdjectiveInterferenceType, dict[str, str]] = {
    AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION: {
        "ua": "Помилка у чергуванні приголосних при творенні вищого ступеня. За Правописом 2019 § 110, приголосні г, ж, з разом із суфіксом -ш- переходять у -жч- (дорожчий, нижчий), а к, с, ст разом із -ш- переходять у -щ- (вищий, товщий).",
        "en": "Consonant mutation error in comparative formation. Under Pravopys 2019 § 110, stems in h, zh, z + -sh- fuse into -zhch- (dorozhchyi, nyzhchyi), and k, s, st + -sh- fuse into -shch- (vyshchyi, tovshchyi).",
    },
    AdjectiveInterferenceType.FALSE_SH_DROPPING_K_MISSING_DROP: {
        "ua": "Помилка при творенні вищого ступеня за допомогою суфікса -ш-. Суфікси -к-, -ок- при цьому обов'язково випадають (Правопис 2019 § 110, п. 1 а: швидкий -> швидший, широкий -> ширший, глибокий -> глибший, а не *швидкший чи *широкший).",
        "en": "Suffix dropping error: suffixes -k- and -ok- strictly drop before comparative suffix -sh- (Pravopys 2019 § 110, item 1 a: shvydkyi -> shvydshyi, shyrokyi -> shyrshyi, not *shvydkshyi).",
    },
    AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH: {
        "ua": "Помилкове вживання суфікса -іш- замість чергування основи з суфіксом -ш-. Суфікс -к- випадає, а кінцевий приголосний зазнає чергування (низький -> нижчий, вузький -> вужчий, високий -> вищий).",
        "en": "Erroneous suffix -ish- used where suffix -k- drops and stem fuses with -sh- (nyzhchyi, vuzhchyi, vyshchyi).",
    },
    AdjectiveInterferenceType.FALSE_COMPARATIVE_SH_FOR_ISH: {
        "ua": "Помилкове приєднання суфікса -ш- безпосередньо до основи, яка вимагає нормативного суфікса -іш- (новий -> новіший, теплий -> тепліший).",
        "en": "Erroneous suffix -sh- attached directly where standard grammar requires -ish- (novishyi, teplishyi).",
    },
    AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED: {
        "ua": "Помилкова спроба утворити ступінь порівняння від початкової основи замість нормативної суплетивної (великий -> більший, малий -> менший, поганий -> гірший, хороший/добрий -> кращий).",
        "en": "Attempting regular formation on suppletive adjectives. Ukrainian uses distinct historical stems: velykyi -> bilshyi, malyi -> menshyi, pohanyi -> hirshyi, dobryi/khoroshyi -> krashchyi.",
    },
    AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE: {
        "ua": "Плеоназм (подвійний вищий ступінь). Не можна поєднувати слова «більш/менш» із простою формою вищого ступеня. Правильно: «більш зручний» або «зручніший», але не «*більш зручніший».",
        "en": "Pleonastic double comparative error. Do not combine 'bilsh/mensh' with a synthetic comparative. Use either 'bilsh zruchnyi' or 'zruchnishyi', never '*bilsh zruchnishyi'.",
    },
    AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI: {
        "ua": "Груба калька з російської мови. Слово «самий» ніколи не вживається в українській мові для творення найвищого ступеня порівняння. Правильно: префікс най- («найкращий», «найбільший») або складена форма («найбільш важливий»).",
        "en": "Severe Russian calque. The word 'samyi' is never used in Ukrainian to form superlatives. Use the prefix nay- (naykrashchyi) or analytic naybilsh + base adjective.",
    },
    AdjectiveInterferenceType.FALSE_SUPERLATIVE_PREFIX_SEPARATED: {
        "ua": "Орфографічна помилка: підсилювальні префікси якнай- та щонай- пишуться з прикметниками разом (якнайшвидший, щонайкращий), а не окремо чи через дефіс.",
        "en": "Orthographic error: emphatic superlative prefixes yaknay- and shchonay- are written solid as one word (yaknayshvydshyi, shchonaykrashchyi).",
    },
    AdjectiveInterferenceType.FALSE_SUPERLATIVE_ANALYTIC_DOUBLE: {
        "ua": "Помилкове поєднання слів «найбільш/найменш» із вищим ступенем замість початкової форми прикметника (правильно: найбільш важливий, а не *найбільш важливіший).",
        "en": "Double superlative error: 'naybilsh/naymensh' must be followed by the positive base form, not the comparative.",
    },
    AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM: {
        "ua": "Помилка у відмінковому закінченні прикметників м'якої групи. В орудному відмінку однини чоловічого та середнього роду прикметники м'якої групи мають закінчення -ім (синім, літнім, осіннім, раннім), а не тверде -им.",
        "en": "Ending error in soft group adjectives. Soft group masculine and neuter instrumental singular strictly takes -im (synim, litnim, osinnim, rannim), not hard -ym.",
    },
    AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING: {
        "ua": "Помилка у відмінюванні м'якої групи прикметників. У родовому відмінку чоловічого роду вони мають закінчення -ього (синього, літнього, давнього), а не тверде -ого.",
        "en": "Soft adjective genitive error. Soft masculine adjectives take -yoho (synyoho, litnyoho), not hard -oho.",
    },
    AdjectiveInterferenceType.FALSE_SOFT_DATIVE_HARD_ENDING: {
        "ua": "Помилка у відмінюванні м'якої групи прикметників. У давальному відмінку чоловічого роду вони мають закінчення -ьому (синьому, літньому), а не тверде -ому.",
        "en": "Soft adjective dative error. Soft masculine adjectives take -yomu (synyomu, litnyomu), not hard -omu.",
    },
    AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION: {
        "ua": "Порушення правил чергування приголосних при творенні присвійних прикметників із суфіксом -ин. Перед -ин приголосні г, к, х чергуються на ж, ч, ш (Ольга -> Ольжин, дочка -> доччин, тітка -> тітчин, Солоха -> Солошин).",
        "en": "Missing consonant alternation before possessive suffix -yn. Consonants h, k, kh mutate to zh, ch, sh (Olha -> Olzhyn, dochka -> dochchyn, Solokha -> Soloshyn).",
    },
    AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL: {
        "ua": "Помилка у голосному суфікса присвійних прикметників. Після м'яких приголосних та [j] виступає суфікс -ев- / -єв- (Василів -> Василева, Сергіїв -> Сергієве), а після твердих — -ов- (батьків -> батькова).",
        "en": "Possessive suffix vowel error. After soft consonants and /j/, suffix -ev- / -yev- is used in open syllables (Vasyleva, Serhiyeva); after hard consonants, -ov- is used (batkova).",
    },
    AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION: {
        "ua": "Порушення правил буквосполучень при творенні прикметників за допомогою суфікса -ськ- (Правопис 2019 § 22): г, ж, з + -ськ- -> -зьк- (Прага -> празький); к, ч, ц + -ськ- -> -цьк- (козак -> козацький); х, ш, с + -ськ- -> -ськ- (чех -> чеський).",
        "en": "Consonant group mutation error with suffix -sk- (Pravopys 2019 § 22): h, zh, z + -sk- -> -zk- (prazkyi); k, ch, ts + -sk- -> -tsk- (kozatskyi); kh, sh, s + -sk- -> -skyi (cheskyi).",
    },
    AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE: {
        "ua": "Помилкове утворення ступенів порівняння від відносного чи якісного прикметника з абсолютною ознакою (матеріал, фізичний стан, час). Такі прикметники не мають ступенів порівняння (дерев'яний, босий, сліпий, вчорашній).",
        "en": "Erroneous degree formation on non-gradable adjectives. Adjectives expressing material, absolute physical state, or time do not form comparative or superlative degrees.",
    },
    AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE: {
        "ua": "Змішування присвійних і відносних прикметників. Для індивідуальної належності одній особі вживаються суфікси -ів, -ин (батьків годинник, Шевченкове слово), тоді як суфікс -ськ- творить відносний прикметник загальної властивості (батьківський, шевченківський).",
        "en": "Confusion between individual possessive (-iv, -yn: batkiv, Shevchenkove) and general relational adjectives (-skyi: batkivskyi, shevchenkivskyi).",
    },
}


@dataclass(frozen=True)
class AdjectiveDistractor:
    text: str
    interference_type: AdjectiveInterferenceType
    explanation: dict[str, str]


@dataclass(frozen=True)
class AdjectiveCard:
    card_id: str
    category: AdjectiveCategory
    cefr_level: str
    prompt_sentence: str
    blank_target: str
    correct_answer: str
    distractors: list[AdjectiveDistractor]
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


# Curated, academically rigorous card definitions covering all 13 categories
CANONICAL_ADJECTIVE_CARDS: list[dict[str, Any]] = [
    # =========================================================================
    # 1. COMP_SYNTHETIC_MUTATION_ZHCH (г, ж, з + -ш- -> -жч-) [§ 110, п. 1 (б)]
    # =========================================================================
    {
        "card_id": "adj_comp_zhch_dorohyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH,
        "cefr_level": "B1",
        "prompt_sentence": "Цей сучасний ноутбук виявився набагато ___, ніж ми розраховували.",
        "blank_target": "дорожчим",
        "correct_answer": "дорожчим",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "Приголосний г разом із суфіксом -ш- чергується на -жч-: дорогий -> дорожчий (в орудному: дорожчим).",
            "en": "Stem consonant h fuses with suffix -sh- into -zhch-: dorohyi -> dorozhchyi (instrumental: dorozhchym).",
        },
        "distractors": [
            ("дорогшим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("дорожшим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("дорожійшим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_zhch_duzhyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH,
        "cefr_level": "B1",
        "prompt_sentence": "Спортсмен повернувся на арену ще ___ та витривалішим.",
        "blank_target": "дужчим",
        "correct_answer": "дужчим",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "Приголосний ж разом із суфіксом -ш- чергується на -жч-: дужий -> дужчий (в орудному: дужчим).",
            "en": "Stem consonant zh fuses with suffix -sh- into -zhch-: duzhyi -> duzhchyi (instrumental: duzhchym).",
        },
        "distractors": [
            ("дужшим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("дужнішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("дужішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_zhch_nyzkyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH,
        "cefr_level": "A2",
        "prompt_sentence": "Новий паркан був значно ___, ніж сусідський кам'яний мур.",
        "blank_target": "нижчий",
        "correct_answer": "нижчий",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У прикметнику низький суфікс -к- випадає, а з разом із -ш- чергується на -жч-: нижчий.",
            "en": "In nyzkyi, suffix -k- drops and z + -sh- mutates into -zhch-: nyzhchyi.",
        },
        "distractors": [
            ("низший", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("низькіший", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("нижійшим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_zhch_vuzkyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH,
        "cefr_level": "B1",
        "prompt_sentence": "Гірська стежка ставала дедалі ___, доки не перетворилася на карниз.",
        "blank_target": "вужчою",
        "correct_answer": "вужчою",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У прикметнику вузький суфікс -к- випадає, а з + -ш- переходить у -жч-: вужча (в орудному: вужчою).",
            "en": "In vuzkyi, suffix -k- drops and z + -sh- becomes -zhch-: vuzhcha (instrumental: vuzhchoyu).",
        },
        "distractors": [
            ("вузшою", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("вузькішою", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("вужнішою", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_zhch_blyzkyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH,
        "cefr_level": "A2",
        "prompt_sentence": "Цей шлях до річки був значно ___, ніж обхідна лісова дорога.",
        "blank_target": "ближчий",
        "correct_answer": "ближчий",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У прикметнику близький суфікс -к- випадає, а з + -ш- чергується на -жч-: ближчий.",
            "en": "In blyzkyi, suffix -k- drops and z + -sh- mutates into -zhch-: blyzhchyi.",
        },
        "distractors": [
            ("близший", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("близькіший", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("ближійший", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_zhch_vazhkyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH,
        "cefr_level": "A2",
        "prompt_sentence": "Другий розділ підручника виявився набагато ___, ніж перший.",
        "blank_target": "важчим",
        "correct_answer": "важчим",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У прикметнику важкий суфікс -к- випадає, а ж + -ш- переходить у -жч-: важчий (в орудному: важчим).",
            "en": "In vazhkyi, suffix -k- drops and zh + -sh- becomes -zhch-: vazhchyi (instrumental: vazhchym).",
        },
        "distractors": [
            ("важшим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("важкіший", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("важійшим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    # =========================================================================
    # 2. COMP_SYNTHETIC_MUTATION_SHCH (к, с, ст + -ш- -> -щ-) [Правопис 2019 § 110, п. 1 (б)]
    # =========================================================================
    {
        "card_id": "adj_comp_shch_vysokyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_SHCH,
        "cefr_level": "A2",
        "prompt_sentence": "Ця нова вежа значно ___, ніж дзвіниця старого монастиря.",
        "blank_target": "вища",
        "correct_answer": "вища",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У слові високий суфікс -ок- випадає, а с разом із суфіксом -ш- переходить у -щ- [шч]: вищий, вища.",
            "en": "In vysokyi, suffix -ok- drops and s + -sh- mutates into -shch-: vyshchyi, vyshcha.",
        },
        "distractors": [
            ("високша", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("високіша", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("вишча", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_comp_shch_vysokyi_masc",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_SHCH,
        "cefr_level": "A2",
        "prompt_sentence": "Хлопець хотів здаватися значно ___, ніж був насправді.",
        "blank_target": "вищим",
        "correct_answer": "вищим",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У прикметнику високий кінцевий приголосний с разом із суфіксом -ш- чергується на -щ-: вищий (в орудному: вищим).",
            "en": "In vysokyi, root consonant s + -sh- mutates into -shch-: vyshchyi (instrumental: vyshchym).",
        },
        "distractors": [
            ("високшим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("високішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("вишчим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_comp_shch_tovstyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_SHCH,
        "cefr_level": "B1",
        "prompt_sentence": "Цей том енциклопедії був набагато ___, ніж академічний довідник.",
        "blank_target": "товщий",
        "correct_answer": "товщий",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У прикметнику товстий кінцеві ст разом із суфіксом -ш- чергуються на -щ-: товщий.",
            "en": "In tovstyi, final st + -sh- mutates into -shch-: tovshchyi.",
        },
        "distractors": [
            ("товстший", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("товжчий", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("товщійший", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_shch_tovstyi_fem",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_SHCH,
        "cefr_level": "B1",
        "prompt_sentence": "Зимова куртка виявилася значно ___, ніж легкий плащ.",
        "blank_target": "товща",
        "correct_answer": "товща",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "У прикметнику товстий кінцеві ст разом із суфіксом -ш- переходять у -щ-: товща (жіночий рід).",
            "en": "In tovstyi, final st + -sh- mutates into -shch-: tovshcha (feminine).",
        },
        "distractors": [
            ("товстша", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("товжча", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("товщійша", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_shch_krashchyi_inst",
        "category": AdjectiveCategory.COMP_SYNTHETIC_MUTATION_SHCH,
        "cefr_level": "A2",
        "prompt_sentence": "Кожен новий проєкт ставав значно ___ результатом тривалої праці.",
        "blank_target": "кращим",
        "correct_answer": "кращим",
        "pravopys_section": "§ 110, п. 1 (б)",
        "rule_summary": {
            "ua": "Форма вищого ступеня кращий містить історичне чергування з суфіксом -ш-, що перейшов у -щ-: кращий (в орудному: кращим).",
            "en": "The comparative form krashchyi features historical mutation yielding -shch-: krashchyi (instrumental: krashchym).",
        },
        "distractors": [
            ("красшим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("красішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("кражчим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    # =========================================================================
    # 2b. COMP_SYNTHETIC_SH_DROPPING_K (Випадання -к-, -ок- перед -ш-) [Правопис 2019 § 110, п. 1 (а)]
    # =========================================================================
    {
        "card_id": "adj_comp_dropk_shvydkyi_inst",
        "category": AdjectiveCategory.COMP_SYNTHETIC_SH_DROPPING_K,
        "cefr_level": "A2",
        "prompt_sentence": "Сучасний експрес є значно ___ транспортом, ніж звичайний автобус.",
        "blank_target": "швидшим",
        "correct_answer": "швидшим",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "У слові швидкий випадає суфікс -к- і додається суфікс -ш-: швидший (в орудному: швидшим, а не *швидкшим).",
            "en": "In shvydkyi, suffix -k- drops before comparative suffix -sh-: shvydshyi (instrumental: shvydshym).",
        },
        "distractors": [
            ("швидкшим", AdjectiveInterferenceType.FALSE_SH_DROPPING_K_MISSING_DROP),
            ("швидкішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("швиджчим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_comp_dropk_shyrokyi_inst",
        "category": AdjectiveCategory.COMP_SYNTHETIC_SH_DROPPING_K,
        "cefr_level": "A2",
        "prompt_sentence": "Внизу за поворотом річище ставало набагато ___.",
        "blank_target": "ширшим",
        "correct_answer": "ширшим",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "У слові широкий випадає суфікс -ок- і додається суфікс -ш-: ширший (в орудному: ширшим, а не *широкшим).",
            "en": "In shyrokyi, suffix -ok- drops before suffix -sh-: shyrshyi (instrumental: shyrshym).",
        },
        "distractors": [
            ("широкшим", AdjectiveInterferenceType.FALSE_SH_DROPPING_K_MISSING_DROP),
            ("широкішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("ширжчим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_comp_dropk_hlybokyi_inst",
        "category": AdjectiveCategory.COMP_SYNTHETIC_SH_DROPPING_K,
        "cefr_level": "B1",
        "prompt_sentence": "У центрі затоки озеро виявилося значно ___.",
        "blank_target": "глибшим",
        "correct_answer": "глибшим",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "У слові глибокий суфікс -ок- випадає перед суфіксом -ш-: глибший (в орудному: глибшим, а не *глибокшим).",
            "en": "In hlybokyi, suffix -ok- drops before suffix -sh-: hlybshyi (instrumental: hlybshym).",
        },
        "distractors": [
            ("глибокшим", AdjectiveInterferenceType.FALSE_SH_DROPPING_K_MISSING_DROP),
            ("глибокішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("глибжчим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_comp_dropk_korotkyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_SH_DROPPING_K,
        "cefr_level": "A2",
        "prompt_sentence": "У грудні світловий день стає значно ___, ніж у листопаді.",
        "blank_target": "коротший",
        "correct_answer": "коротший",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "У прикметнику короткий суфікс -к- випадає перед суфіксом -ш-: коротший (а не *короткший).",
            "en": "In korotkyi, suffix -k- drops before suffix -sh-: korotshyi (not *korotkshyi).",
        },
        "distractors": [
            ("короткший", AdjectiveInterferenceType.FALSE_SH_DROPPING_K_MISSING_DROP),
            ("короткіший", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("корожчий", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    # =========================================================================
    # 3. COMP_SYNTHETIC_ISH (регулярний суфікс -іш-) [§ 110, п. 1 (а)]
    # =========================================================================
    {
        "card_id": "adj_comp_ish_novyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_ISH,
        "cefr_level": "A1",
        "prompt_sentence": "Ця модель смартфона є значно ___, ніж попередня серія.",
        "blank_target": "новішою",
        "correct_answer": "новішою",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "Прикметник новий утворює вищий ступінь за допомогою суфікса -іш-: новіший (в орудному: новішою).",
            "en": "The adjective novyi forms the comparative with suffix -ish-: novishyi (instrumental: novishoyu).",
        },
        "distractors": [
            ("новшою", AdjectiveInterferenceType.FALSE_COMPARATIVE_SH_FOR_ISH),
            ("новжчою", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("новішньою", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_ish_teplyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_ISH,
        "cefr_level": "A1",
        "prompt_sentence": "Сьогоднішній весняний день був набагато ___, ніж учорашній.",
        "blank_target": "тепліший",
        "correct_answer": "тепліший",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "Прикметник теплий приєднує суфікс -іш-: тепліший.",
            "en": "The adjective teplyi attaches suffix -ish-: teplishyi.",
        },
        "distractors": [
            ("тепший", AdjectiveInterferenceType.FALSE_COMPARATIVE_SH_FOR_ISH),
            ("теплячий", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("теплішний", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_ish_rozumnyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_ISH,
        "cefr_level": "B1",
        "prompt_sentence": "Колеги запропонували значно ___ підхід до автоматизації завдань.",
        "blank_target": "розумніший",
        "correct_answer": "розумніший",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "Прикметники з основою на групу приголосних утворюють вищий ступінь лише на -іш-: розумніший.",
            "en": "Adjectives with stems ending in consonant clusters form comparatives strictly with -ish-: rozumnishyi.",
        },
        "distractors": [
            ("розумший", AdjectiveInterferenceType.FALSE_COMPARATIVE_SH_FOR_ISH),
            ("розумнішний", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("розумнійший", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_ish_harnyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_ISH,
        "cefr_level": "A2",
        "prompt_sentence": "Вишитий рушник здався мені ще ___, коли я роздивився візерунок.",
        "blank_target": "гарнішим",
        "correct_answer": "гарнішим",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "Прикметник гарний утворює вищий ступінь за допомогою суфікса -іш-: гарніший (в орудному: гарнішим).",
            "en": "The adjective harnyi forms comparative with suffix -ish-: harnishyi (instrumental: harnishym).",
        },
        "distractors": [
            ("гарншим", AdjectiveInterferenceType.FALSE_COMPARATIVE_SH_FOR_ISH),
            ("гарнійшим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("гарнішним", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_ish_sylnyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_ISH,
        "cefr_level": "A2",
        "prompt_sentence": "Порив вітру в степу став ще ___ та різкішим.",
        "blank_target": "сильнішим",
        "correct_answer": "сильнішим",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "Прикметник сильний утворює форму вищого ступеня за допомогою суфікса -іш-: сильніший.",
            "en": "The adjective sylnyi attaches suffix -ish- for the comparative: sylnishyi.",
        },
        "distractors": [
            ("сильншим", AdjectiveInterferenceType.FALSE_COMPARATIVE_SH_FOR_ISH),
            ("сильнійшим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
            ("сильнішним", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_comp_ish_svizhyi_nom",
        "category": AdjectiveCategory.COMP_SYNTHETIC_ISH,
        "cefr_level": "B1",
        "prompt_sentence": "Після нічної грози повітря в лісі стало набагато ___.",
        "blank_target": "свіжішим",
        "correct_answer": "свіжішим",
        "pravopys_section": "§ 110, п. 1 (а)",
        "rule_summary": {
            "ua": "Прикметник свіжий утворює вищий ступінь за допомогою суфікса -іш-: свіжіший (в орудному: свіжішим).",
            "en": "The adjective svizhyi forms the comparative with suffix -ish-: svizhishyi (instrumental: svizhishym).",
        },
        "distractors": [
            ("свіжшим", AdjectiveInterferenceType.FALSE_COMPARATIVE_SH_FOR_ISH),
            ("свіжчим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
            ("свіжнішим", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    # =========================================================================
    # 4. COMP_SUPPLETIVE (Суплетивні основи) [§ 110, п. 1 (в)]
    # =========================================================================
    {
        "card_id": "adj_comp_supp_velykyi_nom",
        "category": AdjectiveCategory.COMP_SUPPLETIVE,
        "cefr_level": "A1",
        "prompt_sentence": "Нова квартира виявилася значно ___, ніж стара однокімнатна.",
        "blank_target": "більшою",
        "correct_answer": "більшою",
        "pravopys_section": "§ 110, п. 1 (в)",
        "rule_summary": {
            "ua": "Прикметник великий має суплетивну форму вищого ступеня більший (ж.р. більша, в орудному: більшою).",
            "en": "The adjective velykyi forms comparative from suppletive stem bilshyi (fem. instrumental: bilshoyu).",
        },
        "distractors": [
            ("великішою", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("великшою", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("найвеликішою", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
        ],
    },
    {
        "card_id": "adj_comp_supp_malyi_nom",
        "category": AdjectiveCategory.COMP_SUPPLETIVE,
        "cefr_level": "A1",
        "prompt_sentence": "Діаметр цього гвинта був на кілька міліметрів ___ за потрібний.",
        "blank_target": "меншим",
        "correct_answer": "меншим",
        "pravopys_section": "§ 110, п. 1 (в)",
        "rule_summary": {
            "ua": "Прикметник малий має суплетивну форму вищого ступеня менший (в орудному: меншим).",
            "en": "The adjective malyi forms comparative from suppletive stem menshyi (instrumental: menshym).",
        },
        "distractors": [
            ("малішим", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("маленькішим", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("малішним", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
        ],
    },
    {
        "card_id": "adj_comp_supp_pohanyi_nom",
        "category": AdjectiveCategory.COMP_SUPPLETIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Погода восени стала ще ___, ніж була минулого тижня.",
        "blank_target": "гіршою",
        "correct_answer": "гіршою",
        "pravopys_section": "§ 110, п. 1 (в)",
        "rule_summary": {
            "ua": "Прикметник поганий утворює вищий ступінь від іншої основи: гірший (ж.р. гірша, в орудному: гіршою).",
            "en": "The adjective pohanyi forms comparative suppletively: hirshyi (fem. instrumental: hirshoyu).",
        },
        "distractors": [
            ("поганішною", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("поганійшою", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("гіршішою", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
        ],
    },
    {
        "card_id": "adj_comp_supp_dobryi_nom",
        "category": AdjectiveCategory.COMP_SUPPLETIVE,
        "cefr_level": "A1",
        "prompt_sentence": "Новий запропонований варіант видається нам набагато ___.",
        "blank_target": "кращим",
        "correct_answer": "кращим",
        "pravopys_section": "§ 110, п. 1 (в)",
        "rule_summary": {
            "ua": "Прикметники добрий і хороший мають суплетивні форми вищого ступеня кращий та ліпший.",
            "en": "Adjectives dobryi and khoroshyi form suppletive comparatives: krashchyi and lipshyi.",
        },
        "distractors": [
            ("добршим", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("хорошішим", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("добрішним", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
        ],
    },
    {
        "card_id": "adj_comp_supp_lipshyi_gen",
        "category": AdjectiveCategory.COMP_SUPPLETIVE,
        "cefr_level": "B1",
        "prompt_sentence": "У цій складній ситуації годі було знайти ___ порадника, ніж дідусь.",
        "blank_target": "ліпшого",
        "correct_answer": "ліпшого",
        "pravopys_section": "§ 110, п. 1 (в)",
        "rule_summary": {
            "ua": "Суплетивна форма ліпший у родовому відмінку однини має закінчення -ого: ліпшого.",
            "en": "The suppletive comparative lipshyi takes genitive singular ending -oho: lipshoho.",
        },
        "distractors": [
            ("добршого", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("хорошішого", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
            ("ліпнішого", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
        ],
    },
    # =========================================================================
    # 5. COMP_ANALYTIC_FORMATION (Складена форма: більш / менш) [§ 110, п. 2]
    # =========================================================================
    {
        "card_id": "adj_comp_anal_zruchnyi",
        "category": AdjectiveCategory.COMP_ANALYTIC_FORMATION,
        "cefr_level": "B1",
        "prompt_sentence": "Новий графік руху поїздів є ___ для більшості пасажирів.",
        "blank_target": "більш зручним",
        "correct_answer": "більш зручним",
        "pravopys_section": "§ 110, п. 2",
        "rule_summary": {
            "ua": "Складена форма вищого ступеня утворюється за допомогою слів більш/менш і початкової форми прикметника.",
            "en": "The analytic comparative is formed using 'bilsh/mensh' + the positive base form of the adjective.",
        },
        "distractors": [
            ("більш зручнішим", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
            ("саме зручним", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найбільш зручнішим", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
        ],
    },
    {
        "card_id": "adj_comp_anal_dostupnyi",
        "category": AdjectiveCategory.COMP_ANALYTIC_FORMATION,
        "cefr_level": "B1",
        "prompt_sentence": "У віддалених селах цей вид медичних послуг є ___ для населення.",
        "blank_target": "менш доступним",
        "correct_answer": "менш доступним",
        "pravopys_section": "§ 110, п. 2",
        "rule_summary": {
            "ua": "Складена форма з 'менш' вимагає початкової форми прикметника: менш доступний (в орудному: менш доступним).",
            "en": "Analytic form with 'mensh' requires positive degree: mensh dostupnyi (instrumental: mensh dostupnym).",
        },
        "distractors": [
            ("менш доступнішим", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
            ("найменш доступнішим", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
            ("самим доступним", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
        ],
    },
    {
        "card_id": "adj_comp_anal_dosvidchenyi",
        "category": AdjectiveCategory.COMP_ANALYTIC_FORMATION,
        "cefr_level": "B2",
        "prompt_sentence": "Керівником проєкту призначили ___ інженера нашого відділу.",
        "blank_target": "більш досвідченого",
        "correct_answer": "більш досвідченого",
        "pravopys_section": "§ 110, п. 2",
        "rule_summary": {
            "ua": "Складена форма утворюється додаванням слова більш до звичайного прикметника: більш досвідчений.",
            "en": "Analytic comparative is formed by adding 'bilsh' to the positive adjective: bilsh dosvidchenyi.",
        },
        "distractors": [
            ("більш досвідченішого", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
            ("самого досвідченого", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найбільш досвідченішого", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
        ],
    },
    {
        "card_id": "adj_comp_anal_skladnyi",
        "category": AdjectiveCategory.COMP_ANALYTIC_FORMATION,
        "cefr_level": "B1",
        "prompt_sentence": "Друге математичне завдання виявилося ___ за попереднє.",
        "blank_target": "менш складним",
        "correct_answer": "менш складним",
        "pravopys_section": "§ 110, п. 2",
        "rule_summary": {
            "ua": "Слово менш поєднується з початковою формою (складним), а не з вищим ступенем (*складнішим).",
            "en": "The word 'mensh' combines with the base adjective (skladnym), not a synthetic comparative (*skladnishym).",
        },
        "distractors": [
            ("менш складнішим", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
            ("саме складним", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найменш складнішим", AdjectiveInterferenceType.FALSE_DOUBLE_COMPARATIVE),
        ],
    },
    # =========================================================================
    # 6. SUPER_SYNTHETIC_PREFIX (Префікс най-) [§ 111, п. 1]
    # =========================================================================
    {
        "card_id": "adj_super_synth_krashchyi_nom",
        "category": AdjectiveCategory.SUPER_SYNTHETIC_PREFIX,
        "cefr_level": "A1",
        "prompt_sentence": "Він здобув звання ___ знавця української історії.",
        "blank_target": "найкращого",
        "correct_answer": "найкращого",
        "pravopys_section": "§ 111, п. 1",
        "rule_summary": {
            "ua": "Найвищий ступінь утворюється додаванням префікса най- до форми вищого ступеня: найкращий (родов. відм.: найкращого). Калька зі словом «самий» є ненормативною.",
            "en": "Superlative is formed by prefixing nay- to comparative: naykrashchyi (genitive: naykrashchoho). Using 'samyi' is an incorrect calque.",
        },
        "distractors": [
            ("самого кращого", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("самого доброго", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найкраснішого", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
        ],
    },
    {
        "card_id": "adj_super_synth_vysokyi_nom",
        "category": AdjectiveCategory.SUPER_SYNTHETIC_PREFIX,
        "cefr_level": "A2",
        "prompt_sentence": "Говерла — це ___ вершина Українських Карпат.",
        "blank_target": "найвища",
        "correct_answer": "найвища",
        "pravopys_section": "§ 111, п. 1",
        "rule_summary": {
            "ua": "Префікс най- приєднується до форми вищого ступеня (вища): найвища. Конструкції «сама висока/вища» — росіянізми.",
            "en": "Prefix nay- attaches to comparative (vyshcha): nayvyshcha. Phrases like 'sama vysoka' are calques.",
        },
        "distractors": [
            ("сама висока", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("сама вища", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найвисокіша", AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH),
        ],
    },
    {
        "card_id": "adj_super_synth_dorohyi_nom",
        "category": AdjectiveCategory.SUPER_SYNTHETIC_PREFIX,
        "cefr_level": "B1",
        "prompt_sentence": "Спогади дитинства залишилися ___ скарбом у моїй душі.",
        "blank_target": "найдорожчим",
        "correct_answer": "найдорожчим",
        "pravopys_section": "§ 111, п. 1",
        "rule_summary": {
            "ua": "Форма найдорожчий твориться префіксом най- від вищого ступеня дорожчий.",
            "en": "The form naydorozhchyi is built by adding prefix nay- to the comparative dorozhchyi.",
        },
        "distractors": [
            ("самим дорогим", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("самим дорожчим", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найдорогшим", AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_super_synth_velykyi_nom",
        "category": AdjectiveCategory.SUPER_SYNTHETIC_PREFIX,
        "cefr_level": "A1",
        "prompt_sentence": "Це був ___ успіх вітчизняних науковців за останнє десятиліття.",
        "blank_target": "найбільший",
        "correct_answer": "найбільший",
        "pravopys_section": "§ 111, п. 1",
        "rule_summary": {
            "ua": "Префікс най- додається до суплетивного вищого ступеня більший: найбільший.",
            "en": "Prefix nay- attaches to the suppletive comparative bilshyi: naybilshyi.",
        },
        "distractors": [
            ("самий великий", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("самий більший", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найвеликіший", AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED),
        ],
    },
    {
        "card_id": "adj_super_synth_vazhlyvyi_inst",
        "category": AdjectiveCategory.SUPER_SYNTHETIC_PREFIX,
        "cefr_level": "B1",
        "prompt_sentence": "Охорона довкілля залишається ___ пріоритетом для громади.",
        "blank_target": "найважливішим",
        "correct_answer": "найважливішим",
        "pravopys_section": "§ 111, п. 1",
        "rule_summary": {
            "ua": "Префікс най- у поєднанні з формою важливіший утворює синтетичний найвищий ступінь: найважливіший.",
            "en": "Prefix nay- combined with vazhlyvishyi forms synthetic superlative: nayvazhlyvishyi.",
        },
        "distractors": [
            ("самим важливим", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("самим важливішим", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найбільш важливішим", AdjectiveInterferenceType.FALSE_SUPERLATIVE_ANALYTIC_DOUBLE),
        ],
    },
    {
        "card_id": "adj_super_synth_menshyi_inst",
        "category": AdjectiveCategory.SUPER_SYNTHETIC_PREFIX,
        "cefr_level": "A2",
        "prompt_sentence": "Ми вирішили обрати шлях із ___ опором і перешкодами.",
        "blank_target": "найменшим",
        "correct_answer": "найменшим",
        "pravopys_section": "§ 111, п. 1",
        "rule_summary": {
            "ua": "Префікс най- додається до суплетивного ступеня менший: найменший (в орудному: найменшим).",
            "en": "Prefix nay- attaches to suppletive comparative menshyi: naymenshyi (instrumental: naymenshym).",
        },
        "distractors": [
            ("самим меншим", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("самим малим", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
            ("найменш меншим", AdjectiveInterferenceType.FALSE_SUPERLATIVE_ANALYTIC_DOUBLE),
        ],
    },
    # =========================================================================
    # 7. SUPER_EMPHATIC_PREFIX (Підсилювальні префікси якнай-, щонай-) [§ 111, п. 1 (б)]
    # =========================================================================
    {
        "card_id": "adj_super_emph_yaknaishvydshyi",
        "category": AdjectiveCategory.SUPER_EMPHATIC_PREFIX,
        "cefr_level": "B1",
        "prompt_sentence": "Команда повинна знайти ___ вихід зі скрутного становища.",
        "blank_target": "якнайшвидший",
        "correct_answer": "якнайшвидший",
        "pravopys_section": "§ 111, п. 1 (б)",
        "rule_summary": {
            "ua": "Підсилювальні префікси якнай- та щонай- пишуться з формами найвищого ступеня разом: якнайшвидший.",
            "en": "Emphatic prefixes yaknay- and shchonay- are written solid with superlative forms: yaknayshvydshyi.",
        },
        "distractors": [
            ("як найшвидший", AdjectiveInterferenceType.FALSE_SUPERLATIVE_PREFIX_SEPARATED),
            ("як-найшвидший", AdjectiveInterferenceType.FALSE_SUPERLATIVE_PREFIX_SEPARATED),
            ("самий найшвидший", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
        ],
    },
    {
        "card_id": "adj_super_emph_shchonakrashchyi",
        "category": AdjectiveCategory.SUPER_EMPHATIC_PREFIX,
        "cefr_level": "B2",
        "prompt_sentence": "Студенти доклали всіх зусиль, аби показати ___ результати на олімпіаді.",
        "blank_target": "щонайкращі",
        "correct_answer": "щонайкращі",
        "pravopys_section": "§ 111, п. 1 (б)",
        "rule_summary": {
            "ua": "Префікс щонай- пишеться разом: щонайкращий (у множині: щонайкращі).",
            "en": "Prefix shchonay- is written solid as a single word: shchonaykrashchyi (plural: shchonaykrashchi).",
        },
        "distractors": [
            ("що найкращі", AdjectiveInterferenceType.FALSE_SUPERLATIVE_PREFIX_SEPARATED),
            ("що-найкращі", AdjectiveInterferenceType.FALSE_SUPERLATIVE_PREFIX_SEPARATED),
            ("самі щонайкращі", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
        ],
    },
    {
        "card_id": "adj_super_emph_yaknaibilshyi",
        "category": AdjectiveCategory.SUPER_EMPHATIC_PREFIX,
        "cefr_level": "B1",
        "prompt_sentence": "Організатори свята подбали про ___ зручності для відвідувачів.",
        "blank_target": "якнайбільші",
        "correct_answer": "якнайбільші",
        "pravopys_section": "§ 111, п. 1 (б)",
        "rule_summary": {
            "ua": "Префікс якнай- пишеться разом з прикметником: якнайбільший (у множині: якнайбільші).",
            "en": "Prefix yaknay- is written solid with the adjective: yaknaybilshyi (plural: yaknaybilshi).",
        },
        "distractors": [
            ("як найбільші", AdjectiveInterferenceType.FALSE_SUPERLATIVE_PREFIX_SEPARATED),
            ("як-найбільші", AdjectiveInterferenceType.FALSE_SUPERLATIVE_PREFIX_SEPARATED),
            ("самі найбільші", AdjectiveInterferenceType.RUSSIAN_CALQUE_SAMYI),
        ],
    },
    # =========================================================================
    # 8. DECL_SOFT_INSTRUMENTAL_IM (М'яка група: орудний на -ім) [§ 108, п. 1]
    # =========================================================================
    {
        "card_id": "adj_decl_soft_synii_inst",
        "category": AdjectiveCategory.DECL_SOFT_INSTRUMENTAL_IM,
        "cefr_level": "A2",
        "prompt_sentence": "Художник зафарбував небо глибоким ___ кольором.",
        "blank_target": "синім",
        "correct_answer": "синім",
        "pravopys_section": "§ 108, п. 1",
        "rule_summary": {
            "ua": "Прикметники м'якої групи чоловічого та середнього роду в орудному відмінку однини мають закінчення -ім (синім), а не тверде -им.",
            "en": "Soft masculine/neuter adjectives in the instrumental singular strictly take -im (synim), not hard -ym.",
        },
        "distractors": [
            ("синим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("синьовим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("синьми", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
        ],
    },
    {
        "card_id": "adj_decl_soft_litnii_inst",
        "category": AdjectiveCategory.DECL_SOFT_INSTRUMENTAL_IM,
        "cefr_level": "A2",
        "prompt_sentence": "Земля була зігріта ласкавим ___ сонцем.",
        "blank_target": "літнім",
        "correct_answer": "літнім",
        "pravopys_section": "§ 108, п. 1",
        "rule_summary": {
            "ua": "Прикметник м'якої групи літній в орудному відмінку середнього роду має закінчення -ім: літнім.",
            "en": "Soft neuter adjective litnii in instrumental singular takes ending -im: litnim.",
        },
        "distractors": [
            ("літним", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("літньовим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("літнем", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
        ],
    },
    {
        "card_id": "adj_decl_soft_osinnii_inst",
        "category": AdjectiveCategory.DECL_SOFT_INSTRUMENTAL_IM,
        "cefr_level": "A2",
        "prompt_sentence": "Алея була огорнута сивим ___ туманом.",
        "blank_target": "осіннім",
        "correct_answer": "осіннім",
        "pravopys_section": "§ 108, п. 1",
        "rule_summary": {
            "ua": "Прикметник осінній належить до м'якої групи й утворює орудний відмінок однини на -ім: осіннім.",
            "en": "Adjective osinnii is soft group and forms instrumental singular with ending -im: osinnim.",
        },
        "distractors": [
            ("осінним", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("осінневим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("осінньовим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
        ],
    },
    {
        "card_id": "adj_decl_soft_rannii_inst",
        "category": AdjectiveCategory.DECL_SOFT_INSTRUMENTAL_IM,
        "cefr_level": "B1",
        "prompt_sentence": "Мандрівники вирушили в дорогу найпершим ___ потягом.",
        "blank_target": "раннім",
        "correct_answer": "раннім",
        "pravopys_section": "§ 108, п. 1",
        "rule_summary": {
            "ua": "Прикметник ранній в орудному відмінку чоловічого роду однини має закінчення -ім: раннім.",
            "en": "Adjective rannii in masculine instrumental singular takes ending -im: rannim.",
        },
        "distractors": [
            ("ранним", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("ранневим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("ранньовим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
        ],
    },
    {
        "card_id": "adj_decl_soft_vechirnii_inst",
        "category": AdjectiveCategory.DECL_SOFT_INSTRUMENTAL_IM,
        "cefr_level": "A2",
        "prompt_sentence": "Вулиці міста освітилися м'яким ___ сяйвом ліхтарів.",
        "blank_target": "вечірнім",
        "correct_answer": "вечірнім",
        "pravopys_section": "§ 108, п. 1",
        "rule_summary": {
            "ua": "Прикметник вечірній має м'яку основу й закінчення -ім в орудному відмінку: вечірнім.",
            "en": "Adjective vechirnii has a soft stem and takes -im in instrumental: vechirnim.",
        },
        "distractors": [
            ("вечірним", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("вечірневим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("вечірньовим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
        ],
    },
    {
        "card_id": "adj_decl_soft_davnii_inst",
        "category": AdjectiveCategory.DECL_SOFT_INSTRUMENTAL_IM,
        "cefr_level": "B1",
        "prompt_sentence": "Ми зустрілися з моїм ___ шкільним товаришем.",
        "blank_target": "давнім",
        "correct_answer": "давнім",
        "pravopys_section": "§ 108, п. 1",
        "rule_summary": {
            "ua": "Прикметник давній утворює орудний відмінок однини на -ім: давнім.",
            "en": "Adjective davnii takes instrumental singular ending -im: davnim.",
        },
        "distractors": [
            ("давним", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("давневим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("давньовим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
        ],
    },
    {
        "card_id": "adj_decl_soft_krainii_inst",
        "category": AdjectiveCategory.DECL_SOFT_INSTRUMENTAL_IM,
        "cefr_level": "B1",
        "prompt_sentence": "Він зупинився перед ___ під'їздом висотного будинку.",
        "blank_target": "крайнім",
        "correct_answer": "крайнім",
        "pravopys_section": "§ 108, п. 1",
        "rule_summary": {
            "ua": "Прикметник крайній (м'яка група) в орудному відмінку чоловічого роду має закінчення -ім: крайнім.",
            "en": "Soft adjective krainii in masculine instrumental singular takes -im: krainim.",
        },
        "distractors": [
            ("крайним", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("крайневим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
            ("крайньовим", AdjectiveInterferenceType.FALSE_SOFT_INSTRUMENTAL_YM),
        ],
    },
    # =========================================================================
    # 9. DECL_SOFT_GENITIVE_DATIVE (М'яка група: -ього / -ьому) [§ 108]
    # =========================================================================
    {
        "card_id": "adj_decl_soft_synii_gen",
        "category": AdjectiveCategory.DECL_SOFT_GENITIVE_DATIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Для оздоблення картини не вистачало темно-___ барвника.",
        "blank_target": "синього",
        "correct_answer": "синього",
        "pravopys_section": "§ 108",
        "rule_summary": {
            "ua": "Прикметники м'якої групи в родовому відмінку однини мають закінчення -ього: синього (а не тверде -ого).",
            "en": "Soft group adjectives in genitive singular take ending -yoho: synyoho (not hard -oho).",
        },
        "distractors": [
            ("синого", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("синьго", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("синійого", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
        ],
    },
    {
        "card_id": "adj_decl_soft_litnii_gen",
        "category": AdjectiveCategory.DECL_SOFT_GENITIVE_DATIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Ми з нетерпінням очікували початку чергового ___ сезону.",
        "blank_target": "літнього",
        "correct_answer": "літнього",
        "pravopys_section": "§ 108",
        "rule_summary": {
            "ua": "Прикметник літній у родовому відмінку чоловічого роду має закінчення -ього: літнього.",
            "en": "Adjective litnii takes genitive singular ending -yoho: litnyoho.",
        },
        "distractors": [
            ("літного", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("літньго", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("літнійого", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
        ],
    },
    {
        "card_id": "adj_decl_soft_davnii_gen",
        "category": AdjectiveCategory.DECL_SOFT_GENITIVE_DATIVE,
        "cefr_level": "B1",
        "prompt_sentence": "В архіві збереглася точна копія ___ рукописного тексту.",
        "blank_target": "давнього",
        "correct_answer": "давнього",
        "pravopys_section": "§ 108",
        "rule_summary": {
            "ua": "Прикметник давній у родовому відмінку має закінчення -ього: давнього.",
            "en": "Adjective davnii takes genitive singular ending -yoho: davnyoho.",
        },
        "distractors": [
            ("давного", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("давньго", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("давнійого", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
        ],
    },
    {
        "card_id": "adj_decl_soft_synii_dat",
        "category": AdjectiveCategory.DECL_SOFT_GENITIVE_DATIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Дизайнер надав перевагу насиченому ___ відтінку полотна.",
        "blank_target": "синьому",
        "correct_answer": "синьому",
        "pravopys_section": "§ 108",
        "rule_summary": {
            "ua": "Прикметники м'якої групи в давальному відмінку чоловічого роду мають закінчення -ьому: синьому.",
            "en": "Soft group adjectives in masculine dative singular take ending -yomu: synyomu.",
        },
        "distractors": [
            ("синому", AdjectiveInterferenceType.FALSE_SOFT_DATIVE_HARD_ENDING),
            ("синьму", AdjectiveInterferenceType.FALSE_SOFT_DATIVE_HARD_ENDING),
            ("синійому", AdjectiveInterferenceType.FALSE_SOFT_DATIVE_HARD_ENDING),
        ],
    },
    {
        "card_id": "adj_decl_soft_litnii_dat",
        "category": AdjectiveCategory.DECL_SOFT_GENITIVE_DATIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Усі рослини в саду раділи теплому ___ дощу.",
        "blank_target": "літньому",
        "correct_answer": "літньому",
        "pravopys_section": "§ 108",
        "rule_summary": {
            "ua": "Прикметник літній у давальному відмінку однини має закінчення -ьому: літньому.",
            "en": "Adjective litnii in dative singular takes ending -yomu: litnyomu.",
        },
        "distractors": [
            ("літному", AdjectiveInterferenceType.FALSE_SOFT_DATIVE_HARD_ENDING),
            ("літньму", AdjectiveInterferenceType.FALSE_SOFT_DATIVE_HARD_ENDING),
            ("літнійому", AdjectiveInterferenceType.FALSE_SOFT_DATIVE_HARD_ENDING),
        ],
    },
    {
        "card_id": "adj_decl_soft_vechirnii_gen",
        "category": AdjectiveCategory.DECL_SOFT_GENITIVE_DATIVE,
        "cefr_level": "A2",
        "prompt_sentence": "Ми залюбки чекали настання тихого ___ часу для читання.",
        "blank_target": "вечірнього",
        "correct_answer": "вечірнього",
        "pravopys_section": "§ 108",
        "rule_summary": {
            "ua": "Прикметники м'якої групи в родовому відмінку чоловічого роду однини мають закінчення -ього: вечірнього (а не тверде -ого).",
            "en": "Soft-group adjectives in masculine genitive singular take ending -yoho: vechirnyoho (not hard -oho).",
        },
        "distractors": [
            ("вечірного", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("вечірньго", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
            ("вечірнійого", AdjectiveInterferenceType.FALSE_SOFT_GENITIVE_HARD_ENDING),
        ],
    },
    # =========================================================================
    # 10. POSSESSIVE_IV_DECLENSION (Суфікс -ів: -ова, -еве, -єве) [§ 22, 107]
    # =========================================================================
    {
        "card_id": "adj_poss_batkiv_nom",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "A2",
        "prompt_sentence": "На письмовому столі цокав старовинний ___ годинник.",
        "blank_target": "батьків",
        "correct_answer": "батьків",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Присвійний прикметник від іменника II відміни батько твориться суфіксом -ів у називному відмінку чоловічого роду: батьків.",
            "en": "Possessive adjective from 2nd declension batko takes suffix -iv in masculine nominative: batkiv.",
        },
        "distractors": [
            ("батьковий", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("батьківський", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("батьков", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
        ],
    },
    {
        "card_id": "adj_poss_batkiv_gen",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "B1",
        "prompt_sentence": "Ми неухильно дотримувалися суворого ___ наказу.",
        "blank_target": "батькового",
        "correct_answer": "батькового",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Суфікс -ів чергується з -ов- у відкритих складах перед закінченням: батьків -> батькового.",
            "en": "Suffix -iv alternates with -ov- in open syllables before endings: batkiv -> batkovoho.",
        },
        "distractors": [
            ("батьківого", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("батьківського", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("батькового-ж", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
        ],
    },
    {
        "card_id": "adj_poss_shevchenkiv_nom",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "A2",
        "prompt_sentence": "На святі лунало полум'яне й вічне ___ слово.",
        "blank_target": "Шевченкове",
        "correct_answer": "Шевченкове",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Від прізвища Шевченко присвійний прикметник середнього роду твориться суфіксом -ове: Шевченкове слово (а не відносне шевченківське).",
            "en": "From Shevchenko, neuter possessive takes suffix -ove: Shevchenkove slovo (not relational shevchenkivske).",
        },
        "distractors": [
            ("Шевченківське", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("Шевченківе", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("Шевченково", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
        ],
    },
    {
        "card_id": "adj_poss_shevchenkiv_gen",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "B1",
        "prompt_sentence": "Ми зібралися в парку біля підніжжя столітнього ___ дуба.",
        "blank_target": "Шевченкового",
        "correct_answer": "Шевченкового",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Присвійний прикметник у родовому відмінку однини має суфікс -ов- і закінчення -ого: Шевченкового.",
            "en": "Possessive adjective in genitive singular takes suffix -ov- and ending -oho: Shevchenkovoho.",
        },
        "distractors": [
            ("Шевченківого", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("Шевченківського", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("Шевченкового-ж", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
        ],
    },
    {
        "card_id": "adj_poss_frankiv_nom",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "B1",
        "prompt_sentence": "У пам'яті виринула відома крилата ___ фраза про працю.",
        "blank_target": "Франкова",
        "correct_answer": "Франкова",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Від імені Франко присвійний прикметник жіночого роду твориться як Франкова (а не Франківська чи Франківа).",
            "en": "From Franko, feminine possessive is Frankova (not relational Frankivska or non-standard Frankiva).",
        },
        "distractors": [
            ("Франківа", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("Франківська", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("Франковська", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
        ],
    },
    {
        "card_id": "adj_poss_brativ_nom",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "A2",
        "prompt_sentence": "У передпокої стояла новенька дорожня ___ валіза.",
        "blank_target": "братова",
        "correct_answer": "братова",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Присвійний прикметник жіночого роду від брат має суфікс -ов-: братова (а не відносне братська).",
            "en": "Feminine possessive from brat takes suffix -ov-: bratova (not relational bratska).",
        },
        "distractors": [
            ("братіва", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("братська", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("братовська", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
        ],
    },
    {
        "card_id": "adj_poss_vasyliv_nom",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "B1",
        "prompt_sentence": "На журнальному столику лежала улюблена ___ книга.",
        "blank_target": "Василева",
        "correct_answer": "Василева",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Від іменників м'якої групи суфікс -ів у відкритому складі чергується на -ев-: Василь -> Василева (а не Васильова).",
            "en": "From soft stem nouns, suffix -iv in open syllables alternates with -ev-: Vasyl -> Vasyleva (not Vasyliova).",
        },
        "distractors": [
            ("Васильова", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("Василіва", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("Василівська", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
        ],
    },
    {
        "card_id": "adj_poss_serhiiv_nom",
        "category": AdjectiveCategory.POSSESSIVE_IV_DECLENSION,
        "cefr_level": "B1",
        "prompt_sentence": "Перед поїздкою знайшлося забуте службове ___ посвідчення.",
        "blank_target": "Сергієве",
        "correct_answer": "Сергієве",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Від іменників з основою на [j] у відкритому складі вживається суфікс -єв-: Сергій -> Сергієве посвідчення.",
            "en": "From stems in /j/, suffix -yev- is used in open syllables: Serhiy -> Serhiyeve posvidchennya.",
        },
        "distractors": [
            ("Сергійове", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
            ("Сергієвське", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("Сергіїве", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
        ],
    },
    # =========================================================================
    # 11. POSSESSIVE_YN_MUTATION (Чергування г->ж, к->ч, х->ш перед -ин) [§ 22, 107]
    # =========================================================================
    {
        "card_id": "adj_poss_olzhyn_nom",
        "category": AdjectiveCategory.POSSESSIVE_YN_MUTATION,
        "cefr_level": "A2",
        "prompt_sentence": "На полиці шафи стояв новенький ___ щоденник.",
        "blank_target": "Ольжин",
        "correct_answer": "Ольжин",
        "pravopys_section": "§ 22, 107",
        "rule_summary": {
            "ua": "Перед суфіксом -ин приголосний г чергується на ж: Ольга -> Ольжин щоденник (а не *Ольгин).",
            "en": "Before suffix -yn, consonant h mutates into zh: Olha -> Olzhyn (not *Olhyn).",
        },
        "distractors": [
            ("Ольгин", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("Ольжчин", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("Ольгів", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
        ],
    },
    {
        "card_id": "adj_poss_dochchyn_acc",
        "category": AdjectiveCategory.POSSESSIVE_YN_MUTATION,
        "cefr_level": "A2",
        "prompt_sentence": "Мати дбайливо прасувала святкову ___ сукню.",
        "blank_target": "доччину",
        "correct_answer": "доччину",
        "pravopys_section": "§ 22, 107",
        "rule_summary": {
            "ua": "Перед суфіксом -ин кінцевий к чергується на ч: дочка -> доччин (знах. відм.: доччину).",
            "en": "Before suffix -yn, stem k mutates to ch: dochka -> dochchyn (accusative: dochchynu).",
        },
        "distractors": [
            ("дочкину", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("дочкин", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("дочечну", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_poss_titchyn_acc",
        "category": AdjectiveCategory.POSSESSIVE_YN_MUTATION,
        "cefr_level": "A2",
        "prompt_sentence": "Малюки залюбки слухали повчальну ___ казку.",
        "blank_target": "тітчину",
        "correct_answer": "тітчину",
        "pravopys_section": "§ 22, 107",
        "rule_summary": {
            "ua": "Перед суфіксом -ин кінцевий к основи чергується на ч: тітка -> тітчин (знах. відм.: тітчину).",
            "en": "Before suffix -yn, stem k mutates to ch: titka -> titchyn (accusative: titchynu).",
        },
        "distractors": [
            ("тіткину", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("тітчену", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("тітчинську", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
        ],
    },
    {
        "card_id": "adj_poss_kachchyn_nom",
        "category": AdjectiveCategory.POSSESSIVE_YN_MUTATION,
        "cefr_level": "B1",
        "prompt_sentence": "У високій траві біліло маленьке ___ крильце.",
        "blank_target": "каччине",
        "correct_answer": "каччине",
        "pravopys_section": "§ 22, 107",
        "rule_summary": {
            "ua": "Перед суфіксом -ин приголосний к основи чергується на ч: качка -> каччин (середній рід: каччине).",
            "en": "Before suffix -yn, stem k mutates to ch: kachka -> kachchyn (neuter: kachchyne).",
        },
        "distractors": [
            ("качкине", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("каччене", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("каччинське", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
        ],
    },
    {
        "card_id": "adj_poss_soloshyn_nom",
        "category": AdjectiveCategory.POSSESSIVE_YN_MUTATION,
        "cefr_level": "B2",
        "prompt_sentence": "У фольклорній виставі з'явився колоритний ___ образ.",
        "blank_target": "Солошин",
        "correct_answer": "Солошин",
        "pravopys_section": "§ 22, 107",
        "rule_summary": {
            "ua": "Перед суфіксом -ин кінцевий х чергується на ш: Солоха -> Солошин (а не *Солохин).",
            "en": "Before suffix -yn, stem kh mutates to sh: Solokha -> Soloshyn (not *Solokhyn).",
        },
        "distractors": [
            ("Солохин", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("Солошинський", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("Солохів", AdjectiveInterferenceType.FALSE_POSSESSIVE_IV_SUFFIX_VOWEL),
        ],
    },
    {
        "card_id": "adj_poss_svekrushyn_nom",
        "category": AdjectiveCategory.POSSESSIVE_YN_MUTATION,
        "cefr_level": "B1",
        "prompt_sentence": "У родині завжди шанували розважливий ___ голос.",
        "blank_target": "свекрушин",
        "correct_answer": "свекрушин",
        "pravopys_section": "§ 22, 107",
        "rule_summary": {
            "ua": "Перед суфіксом -ин кінцевий приголосний х чергується на ш: свекруха -> свекрушин (а не *свекрухин).",
            "en": "Before suffix -yn, stem kh mutates to sh: svekrukha -> svekrushyn (not *svekrukhyn).",
        },
        "distractors": [
            ("свекрухин", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("свекрушен", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("свекрушинський", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
        ],
    },
    {
        "card_id": "adj_poss_mariin_nom",
        "category": AdjectiveCategory.POSSESSIVE_YN_MUTATION,
        "cefr_level": "A2",
        "prompt_sentence": "У кімнаті несподівано пролунав дзвінкий ___ сміх.",
        "blank_target": "Маріїн",
        "correct_answer": "Маріїн",
        "pravopys_section": "§ 107",
        "rule_summary": {
            "ua": "Після голосного [j] суфікс -ин позначається літерою ї: Марія -> Маріїн сміх.",
            "en": "After vowel /j/, suffix -yn is spelled with letter yi: Mariya -> Mariyin.",
        },
        "distractors": [
            ("Марійн", AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION),
            ("Марієвий", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
            ("Маріївський", AdjectiveInterferenceType.FALSE_RELATIONAL_FOR_POSSESSIVE),
        ],
    },
    # =========================================================================
    # 12. SUFFIX_DERIVATION_MUTATION (-ськ-, -цьк-, -зьк-) [§ 22]
    # =========================================================================
    {
        "card_id": "adj_deriv_prazkyi_gen",
        "category": AdjectiveCategory.SUFFIX_DERIVATION_MUTATION,
        "cefr_level": "B1",
        "prompt_sentence": "У галереї триває виставка робіт відомих ___ художників.",
        "blank_target": "празьких",
        "correct_answer": "празьких",
        "pravopys_section": "§ 22",
        "rule_summary": {
            "ua": "Приголосний г разом із -ськ- чергується на -зьк-: Прага -> празький (родов. множ.: празьких).",
            "en": "Stem h + -sk- mutates into -zk-: Praha -> prazkyi (genitive plural: prazkykh).",
        },
        "distractors": [
            ("прагських", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("пражських", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("працьких", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_deriv_zaporizkyi_gen",
        "category": AdjectiveCategory.SUFFIX_DERIVATION_MUTATION,
        "cefr_level": "B1",
        "prompt_sentence": "Студенти докладно вивчали героїчну добу ___ козацтва.",
        "blank_target": "запорізького",
        "correct_answer": "запорізького",
        "pravopys_section": "§ 22",
        "rule_summary": {
            "ua": "Приголосний ж разом із -ськ- чергується на -зьк-: Запоріжжя -> запорізький.",
            "en": "Stem zh + -sk- mutates into -zk-: Zaporizhzhya -> zaporizkyi.",
        },
        "distractors": [
            ("запоріжського", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("запоріжжського", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("запоріцького", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_deriv_kozatskyi_nom",
        "category": AdjectiveCategory.SUFFIX_DERIVATION_MUTATION,
        "cefr_level": "A2",
        "prompt_sentence": "Над широким Дніпром лунала відважна ___ пісня.",
        "blank_target": "козацька",
        "correct_answer": "козацька",
        "pravopys_section": "§ 22",
        "rule_summary": {
            "ua": "Приголосний к разом із -ськ- чергується на -цьк-: козак -> козацький, козацька.",
            "en": "Stem k + -sk- mutates into -tsk-: kozak -> kozatskyi, kozatska.",
        },
        "distractors": [
            ("козакська", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("козажська", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("козазька", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_deriv_tkatskyi_nom",
        "category": AdjectiveCategory.SUFFIX_DERIVATION_MUTATION,
        "cefr_level": "B1",
        "prompt_sentence": "У старому музеї ремесел зберігся справжній ___ верстат.",
        "blank_target": "ткацький",
        "correct_answer": "ткацький",
        "pravopys_section": "§ 22",
        "rule_summary": {
            "ua": "Приголосний ч разом із -ськ- чергується на -цьк-: ткач -> ткацький.",
            "en": "Stem ch + -sk- mutates into -tsk-: tkach -> tkatskyi.",
        },
        "distractors": [
            ("ткачський", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("ткажський", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("тказький", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_deriv_cheskyi_nom",
        "category": AdjectiveCategory.SUFFIX_DERIVATION_MUTATION,
        "cefr_level": "A2",
        "prompt_sentence": "В університеті відкрили відділення ___ філології.",
        "blank_target": "чеської",
        "correct_answer": "чеської",
        "pravopys_section": "§ 22",
        "rule_summary": {
            "ua": "Приголосний х разом із -ськ- дає -ськ-: чех -> чеський (родов. відм. ж.р.: чеської).",
            "en": "Stem kh + -sk- yields -sk-: chekh -> cheskyi (fem. genitive: cheskoyi).",
        },
        "distractors": [
            ("чехської", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("чешської", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("чезької", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
        ],
    },
    {
        "card_id": "adj_deriv_tovaryskyi_nom",
        "category": AdjectiveCategory.SUFFIX_DERIVATION_MUTATION,
        "cefr_level": "B1",
        "prompt_sentence": "У новому колективі панували щирі ___ взаємини.",
        "blank_target": "товариські",
        "correct_answer": "товариські",
        "pravopys_section": "§ 22",
        "rule_summary": {
            "ua": "Приголосний ш разом із -ськ- переходить у -ськ-: товариш -> товариський.",
            "en": "Stem sh + -sk- yields -sk-: tovarysh -> tovaryskyi.",
        },
        "distractors": [
            ("товаришські", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("товарижські", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
            ("товаризькі", AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION),
        ],
    },
    # =========================================================================
    # 13. ANTI_CALQUE_UNCOMPARABLE (Прикметники без ступенів порівняння) [§ 110]
    # =========================================================================
    {
        "card_id": "adj_uncomp_derevianyj",
        "category": AdjectiveCategory.ANTI_CALQUE_UNCOMPARABLE,
        "cefr_level": "B1",
        "prompt_sentence": "Оберіть правильне твердження щодо прикметника «дерев'яний» (стіл):",
        "blank_target": "не має ступенів порівняння",
        "correct_answer": "Не має ступенів порівняння, оскільки виражає абсолютну ознаку матеріалу",
        "pravopys_section": "§ 110",
        "rule_summary": {
            "ua": "Відносні прикметники, які називають матеріал (дерев'яний, залізний), не мають ступенів порівняння.",
            "en": "Relational adjectives denoting material (derev'yanyi, zaliznyi) do not form comparative degrees.",
        },
        "distractors": [
            ("Утворює синтетичну форму «дерев'яніший»", AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE),
            ("Утворює аналітичну форму «більш дерев'яний»", AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE),
            ("Утворює найвищий ступінь «найдерев'яніший»", AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE),
        ],
    },
    {
        "card_id": "adj_uncomp_bosyi",
        "category": AdjectiveCategory.ANTI_CALQUE_UNCOMPARABLE,
        "cefr_level": "B1",
        "prompt_sentence": "Оберіть нормативне твердження щодо прикметника «босий»:",
        "blank_target": "не утворює ступенів порівняння",
        "correct_answer": "Не утворює ступенів порівняння, бо виражає абсолютний фізичний стан",
        "pravopys_section": "§ 110",
        "rule_summary": {
            "ua": "Якісні прикметники з абсолютною ознакою або станом (босий, голий, сліпий, мертвий) не підлягають градуюванню.",
            "en": "Qualitative adjectives denoting absolute states (bosyi, slipyi, mertvyi) cannot be graded.",
        },
        "distractors": [
            (
                "Нормативною є форма вищого ступеня «босіший»",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
            ("Нормативною є складена форма «більш босий»", AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE),
            (
                "Нормативною є форма найвищого ступеня «найбосіший»",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
        ],
    },
    {
        "card_id": "adj_uncomp_slipyi",
        "category": AdjectiveCategory.ANTI_CALQUE_UNCOMPARABLE,
        "cefr_level": "B2",
        "prompt_sentence": "Чи можна утворити ступінь порівняння від прикметника «сліпий» у прямому значенні?",
        "blank_target": "ні, це абсолютна ознака",
        "correct_answer": "Ні, бо це абсолютна фізіологічна ознака, яка не виявляється більшою чи меншою мірою",
        "pravopys_section": "§ 110",
        "rule_summary": {
            "ua": "Прикметники на позначення абсолютної фізіологічної якості не утворюють ступенів порівняння.",
            "en": "Adjectives expressing absolute physiological conditions do not form degrees of comparison.",
        },
        "distractors": [
            (
                "Так, правильною є синтетична форма «сліпіший»",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
            (
                "Так, правильною є аналітична форма «більш сліпий»",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
            (
                "Так, правильною є форма найвищого ступеня «найсліпіший»",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
        ],
    },
    {
        "card_id": "adj_uncomp_vchorashnii",
        "category": AdjectiveCategory.ANTI_CALQUE_UNCOMPARABLE,
        "cefr_level": "B1",
        "prompt_sentence": "Оберіть правильну граматичну характеристику прикметника «вчорашній»:",
        "blank_target": "відносний часовий прикметник",
        "correct_answer": "Це відносний часовий прикметник, який не має ступенів порівняння",
        "pravopys_section": "§ 110",
        "rule_summary": {
            "ua": "Відносні часові прикметники (вчорашній, торішній, ранковий) не мають ступенів порівняння.",
            "en": "Temporal relational adjectives (vchorashnii, torishnii, rankovyi) do not have degrees of comparison.",
        },
        "distractors": [
            ("Має форму вищого ступеня «вчорашніший»", AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE),
            ("Має складену форму «більш вчорашній»", AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE),
            (
                "Має форму найвищого ступеня «найвчорашніший»",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
        ],
    },
    {
        "card_id": "adj_uncomp_zaliznyi",
        "category": AdjectiveCategory.ANTI_CALQUE_UNCOMPARABLE,
        "cefr_level": "B1",
        "prompt_sentence": "Чому прикметник «залізний» (паркан) не утворює форми «залізніший»?",
        "blank_target": "відносний прикметник на позначення матеріалу",
        "correct_answer": "Тому що це відносний прикметник на позначення матеріалу",
        "pravopys_section": "§ 110",
        "rule_summary": {
            "ua": "Прикметники, що вказують на матеріал предмета, належать до розряду відносних і не утворюють ступенів порівняння.",
            "en": "Adjectives indicating material belong to the relational category and cannot form degrees of comparison.",
        },
        "distractors": [
            (
                "Тому що основа закінчується на групу приголосних -зн-",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
            (
                "Тому що він вимагає складеної форми «більш залізний»",
                AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE,
            ),
            ("Тому що це прикметник м'якої групи", AdjectiveInterferenceType.FALSE_COMPARISON_OF_UNCOMPARABLE),
        ],
    },
]


def build_card(raw: dict[str, Any]) -> AdjectiveCard:
    """Builds a verified AdjectiveCard ensuring zero option collisions."""
    correct_answer = raw["correct_answer"]
    raw_distractors = raw["distractors"]

    distractor_objs: list[AdjectiveDistractor] = []
    seen_texts: set[str] = {correct_answer.strip()}

    for text, interference_type in raw_distractors:
        norm_text = text.strip()
        if norm_text in seen_texts:
            raise ValueError(f"Collision detected in card {raw['card_id']}: duplicate option '{norm_text}'")
        seen_texts.add(norm_text)
        explanation = INTERFERENCE_EXPLANATIONS[interference_type]
        distractor_objs.append(
            AdjectiveDistractor(
                text=norm_text,
                interference_type=interference_type,
                explanation=explanation,
            )
        )

    return AdjectiveCard(
        card_id=raw["card_id"],
        category=raw["category"],
        cefr_level=raw["cefr_level"],
        prompt_sentence=raw["prompt_sentence"],
        blank_target=raw["blank_target"],
        correct_answer=correct_answer,
        distractors=distractor_objs,
        pravopys_section=raw["pravopys_section"],
        rule_summary=raw["rule_summary"],
    )


def validate_adjective_card(card: AdjectiveCard) -> list[str]:
    """Validates card properties and guarantees zero option collisions."""
    errors: list[str] = []
    if not card.card_id:
        errors.append("Missing card_id")
    if not card.prompt_sentence:
        errors.append("Missing prompt_sentence")
    if card.category != AdjectiveCategory.ANTI_CALQUE_UNCOMPARABLE and "___" not in card.prompt_sentence:
        errors.append(f"Prompt sentence lacks blank marker '___': {card.prompt_sentence}")
    if not card.correct_answer:
        errors.append("Missing correct_answer")
    if len(card.distractors) != 3:
        errors.append(f"Expected 3 distractors, found {len(card.distractors)}")
    opts = card.all_options()
    if len(opts) != 4:
        errors.append(f"Expected 4 options, found {len(opts)}")
    if len(set(opts)) != 4:
        errors.append(f"Option collision in {card.card_id}: {opts}")
    if card.correct_answer not in opts:
        errors.append("correct_answer not in options")
    return errors


def build_canonical_adjective_cards() -> list[AdjectiveCard]:
    """Generates all canonical cards deterministically."""
    return [build_card(raw) for raw in CANONICAL_ADJECTIVE_CARDS]


def generate_deck(seed: int = 42) -> list[AdjectiveCard]:
    """Backwards-compatible alias for build_canonical_adjective_cards."""
    return build_canonical_adjective_cards()


def resolve_degree_comparison_rule(
    category: AdjectiveCategory,
) -> tuple[str, str, str]:
    """Resolves degree of comparison formation rule."""
    if category == AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH:
        return (
            "-жч-",
            "При творенні вищого ступеня приголосні г, ж, з разом із суфіксом -ш- переходять у -жч- (Правопис 2019 § 110, п. 1 б: дорожчий, ближчий, вужчий).",
            "In comparative formation, stems ending in h, zh, z fuse with suffix -sh- to form -zhch- (Pravopys 2019 § 110, item 1 b: dorozhchyi, blyzhchyi, vuzhchyi).",
        )
    if category == AdjectiveCategory.COMP_SYNTHETIC_MUTATION_SHCH:
        return (
            "-щ-",
            "При творенні вищого ступеня приголосні к, с разом із суфіксом -ш- переходять у -щ- (Правопис 2019 § 110, п. 1 б: вищий, товщий, кращий).",
            "In comparative formation, stems ending in k, s fuse with suffix -sh- to form -shch- (Pravopys 2019 § 110, item 1 b: vyshchyi, tovshchyi).",
        )
    if category == AdjectiveCategory.COMP_SYNTHETIC_SH_DROPPING_K:
        return (
            "-ш- (випадання -к-/-ок-)",
            "При творенні вищого ступеня за допомогою суфікса -ш- суфікси -к-, -ок- випадають (Правопис 2019 § 110, п. 1 а: швидкий -> швидший, широкий -> ширший, глибокий -> глибший, короткий -> коротший).",
            "When forming the comparative with suffix -sh-, suffixes -k- and -ok- drop (Pravopys 2019 § 110, item 1 a: shvydkyi -> shvydshyi, shyrokyi -> shyrshyi, hlybokyi -> hlybshyi).",
        )
    if category == AdjectiveCategory.COMP_SYNTHETIC_ISH:
        return (
            "-іш-",
            "Більшість якісних прикметників утворюють вищий ступінь за допомогою суфікса -іш- (Правопис 2019 § 110, п. 1 а: новіший, тепліший, розумніший).",
            "Most qualitative adjectives form the comparative with suffix -ish- (Pravopys 2019 § 110, item 1 a: novishyi, teplishyi).",
        )
    if category == AdjectiveCategory.COMP_SUPPLETIVE:
        return (
            "Суплетивна основа",
            "Деякі якісні прикметники утворюють ступені від інших основ (Правопис 2019 § 110, п. 1 в: великий -> більший, малий -> менший, поганий -> гірший, добрий -> кращий).",
            "Suppletive adjectives use entirely different stems for comparison (Pravopys 2019 § 110, item 1 c: velykyi -> bilshyi, malyi -> menshyi).",
        )
    if category == AdjectiveCategory.COMP_ANALYTIC_FORMATION:
        return (
            "більш / менш + звичайна форма",
            "Складена форма вищого ступеня утворюється сполученням слів «більш / менш» із початковою формою (Правопис 2019 § 110, п. 2: більш зручний, не *більш зручніший).",
            "Analytic comparatives are formed by adding 'bilsh / mensh' to the positive base adjective (Pravopys 2019 § 110, item 2).",
        )
    if category == AdjectiveCategory.SUPER_SYNTHETIC_PREFIX:
        return (
            "най- + вищий ступінь",
            "Найвищий ступінь утворюється додаванням префікса най- до форми вищого ступеня (Правопис 2019 § 111, п. 1: найкращий, найвищий; ніколи не *самий кращий).",
            "Synthetic superlatives add prefix nay- to the comparative form (Pravopys 2019 § 111, item 1; never *samyi krashchyi).",
        )
    if category == AdjectiveCategory.SUPER_EMPHATIC_PREFIX:
        return (
            "якнай- / щонай-",
            "Для підсилення значення найвищого ступеня вживаються префікси якнай-, щонай-, що пишуться разом (Правопис 2019 § 111, п. 1 б: якнайшвидший, щонайкращий).",
            "Emphatic prefixes yaknay- and shchonay- are written solid to intensify the superlative (Pravopys 2019 § 111, item 1 b).",
        )
    return ("нормативна форма", "Нормативне творення прикметника.", "Standard adjective formation.")


def resolve_soft_declension_instrumental_rule() -> tuple[str, str, str]:
    """Resolves soft group masculine/neuter singular instrumental ending."""
    return (
        "-ім",
        "Прикметники м'якої групи чоловічого та середнього роду в орудному відмінку однини мають закінчення -ім (Правопис 2019 § 108: синім, літнім, осіннім, раннім).",
        "Soft group masculine and neuter adjectives in the instrumental singular strictly take ending -im (Pravopys 2019 § 108: synim, litnim).",
    )


def resolve_possessive_suffix_rule(
    base_noun_declension: int,
) -> tuple[str, str, str]:
    """Resolves possessive adjective suffix and mutation rules."""
    if base_noun_declension == 1:
        return (
            "-ин / -їн з чергуванням г->ж, к->ч, х->ш",
            "Присвійні прикметники від іменників I відміни утворюються за допомогою суфікса -ин (після голосних -їн), при цьому приголосні г, к, х чергуються на ж, ч, ш (Правопис 2019 § 107: Ольга -> Ольжин, дочка -> доччин, мачуха -> мачушин).",
            "Possessive adjectives from 1st declension nouns take suffix -yn with consonant mutations h->zh, k->ch, kh->sh (Pravopys 2019 § 107).",
        )
    return (
        "-ів (-ова, -еве)",
        "Присвійні прикметники від іменників II відміни утворюються за допомогою суфікса -ів (у непрямих відмінках -ов- після твердих, -ев-/-єв- після м'яких: батьків/батькова, Василів/Василева) (Правопис 2019 § 107).",
        "Possessive adjectives from 2nd declension nouns take suffix -iv (with -ov- / -ev- in inflected forms) (Pravopys 2019 § 107).",
    )


def resolve_derivational_suffix_mutation_rule(stem_consonant_group: str) -> tuple[str, str, str]:
    """Resolves derivational suffix -ськ- mutations (§ 22)."""
    if stem_consonant_group in ("г", "ж", "з"):
        return (
            "-зьк-",
            "При творенні прикметників за допомогою суфікса -ськ- приголосні г, ж, з змінюються на -зьк- (Правопис 2019 § 22: Прага -> празький, Запоріжжя -> запорізький).",
            "Stems in h, zh, z + -sk- mutate into -zk- (Pravopys 2019 § 22: Praha -> prazkyi).",
        )
    if stem_consonant_group in ("к", "ч", "ц"):
        return (
            "-цьк-",
            "При творенні прикметників за допомогою суфікса -ськ- приголосні к, ч, ц змінюються на -цьк- (Правопис 2019 § 22: козак -> козацький, ткач -> ткацький).",
            "Stems in k, ch, ts + -sk- mutate into -tsk- (Pravopys 2019 § 22: kozak -> kozatskyi).",
        )
    return (
        "-ськ-",
        "При творенні прикметників за допомогою суфікса -ськ- приголосні х, ш, с зберігаються: -ськ- (Правопис 2019 § 22: чех -> чеський, товариш -> товариський).",
        "Stems in kh, sh, s + -sk- form -skyi (Pravopys 2019 § 22: chekh -> cheskyi).",
    )


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
        if c.exists():
            return c
    return specified or (PROJECT_ROOT / "data" / "vesum.db")


def verify_deck_with_vesum(cards: list[AdjectiveCard], vesum_db_path: Path | None = None) -> dict[str, Any]:
    """Verifies that target word forms in fill-in-blank cards exist in VESUM."""
    resolved_path = find_vesum_db(vesum_db_path)
    if not resolved_path.exists():
        return {
            "verified": False,
            "error": f"VESUM database not found at {resolved_path}",
            "missing_forms": [],
        }

    conn = sqlite3.connect(resolved_path)
    cur = conn.cursor()

    missing_forms: list[dict[str, str]] = []
    checked_count = 0

    for card in cards:
        # Skip full sentence options in uncomparable explanations
        if card.category == AdjectiveCategory.ANTI_CALQUE_UNCOMPARABLE:
            continue

        target = card.correct_answer.strip()
        # If the target is compound (e.g. 'більш зручним'), check each component
        words = target.split()
        for word in words:
            # Clean punctuation if any
            clean_word = word.strip(".,;:!?«»\"'")
            if not clean_word:
                continue
            checked_count += 1
            cur.execute(
                "SELECT lemma, pos, tags FROM forms_all WHERE word_form = ?",
                (clean_word,),
            )
            rows = cur.fetchall()
            if not rows:
                missing_forms.append(
                    {
                        "card_id": card.card_id,
                        "word": clean_word,
                        "target_answer": target,
                    }
                )

    conn.close()
    return {
        "verified": len(missing_forms) == 0,
        "checked_word_count": checked_count,
        "missing_forms": missing_forms,
    }


def verify_distractors_with_vesum(cards: list[AdjectiveCard], vesum_db_path: Path | None = None) -> dict[str, Any]:
    """Verifies that phonological and morphological corruption distractors are not valid standard words in VESUM."""
    resolved_path = find_vesum_db(vesum_db_path)
    if not resolved_path.exists():
        return {
            "verified": False,
            "error": f"VESUM database not found at {resolved_path}",
            "invalid_distractors": [],
        }

    corruption_types = {
        AdjectiveInterferenceType.FALSE_SYNTHETIC_MISSING_MUTATION,
        AdjectiveInterferenceType.FALSE_SH_DROPPING_K_MISSING_DROP,
        AdjectiveInterferenceType.FALSE_COMPARATIVE_ISH_FOR_SH,
        AdjectiveInterferenceType.FALSE_SUPPLETIVE_REGULARIZED,
        AdjectiveInterferenceType.FALSE_POSSESSIVE_MISSING_MUTATION,
        AdjectiveInterferenceType.FALSE_DERIVATION_MISSING_MUTATION,
    }

    conn = sqlite3.connect(resolved_path)
    cur = conn.cursor()

    invalid_distractors: list[dict[str, Any]] = []
    checked_count = 0

    for card in cards:
        for dist in card.distractors:
            if dist.interference_type in corruption_types:
                clean_word = dist.text.strip(".,;:!?«»\"'")
                checked_count += 1
                cur.execute(
                    "SELECT lemma, pos, tags FROM forms_all WHERE word_form = ?",
                    (clean_word,),
                )
                rows = cur.fetchall()
                standard_adj_rows = [r for r in rows if r[1].startswith("adj") and ":bad" not in r[2]]
                if standard_adj_rows:
                    invalid_distractors.append(
                        {
                            "card_id": card.card_id,
                            "distractor": dist.text,
                            "interference_type": dist.interference_type.value,
                            "matching_vesum_rows": standard_adj_rows,
                        }
                    )

    conn.close()
    return {
        "verified": len(invalid_distractors) == 0,
        "checked_distractor_count": checked_count,
        "invalid_distractors": invalid_distractors,
    }


def export_deck_json(cards: list[AdjectiveCard], output_path: Path) -> None:
    """Exports the generated deck to structured JSON."""
    payload = {
        "version": "1.0.0",
        "title": "Ukrainian Adjective Deep Mechanics Deck (Прикметник)",
        "description": "Comprehensive practice deck for degrees of comparison, soft/hard declension, and possessive formation grounded in Ukrainian Pravopys 2019 §§ 22, 106–114.",
        "card_count": len(cards),
        "cards": [card.to_dict() for card in cards],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def export_adjective_mechanics_deck(output_path: Path) -> Path:
    """Convenience helper exporting all canonical adjective cards to output_path."""
    cards = build_canonical_adjective_cards()
    export_deck_json(cards, output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Adjective Deep Mechanics Practice Engine")
    parser.add_argument(
        "--deck-output",
        type=Path,
        default=PROJECT_ROOT / "registry" / "practice" / "adjective_mechanics_deck.json",
        help="Path to output deck JSON file",
    )
    parser.add_argument(
        "--verify-vesum",
        action="store_true",
        default=True,
        help="Verify target words against data/vesum.db",
    )
    parser.add_argument(
        "--vesum-db",
        type=Path,
        default=None,
        help="Path to vesum.db (defaults to auto-discovered location)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for option ordering")
    args = parser.parse_args()

    cards = generate_deck(seed=args.seed)
    print(f"Generated {len(cards)} canonical adjective mechanics cards.")

    if args.verify_vesum:
        report = verify_deck_with_vesum(cards, args.vesum_db)
        if not report["verified"]:
            print(f"VESUM verification FAILED: missing forms: {report.get('missing_forms', [])}")
            return 1
        print(f"VESUM verification PASSED: {report['checked_word_count']} words verified.")

    export_deck_json(cards, args.deck_output)
    print(f"Exported deck to {args.deck_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
