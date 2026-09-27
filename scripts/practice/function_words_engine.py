"""Ukrainian Function Words Practice Engine (Службові частини мови).

Implements Ukrainian Pravopys 2019 (§§ 42–44) and Academic Grammar rules for:
  1. Prepositions (Прийменники):
     - Solid compound prepositions (§ 42, п. 1: посеред, задля, заради, внаслідок, напередодні).
     - Compound prepositions with з-/із- via hyphen (§ 42, п. 2: з-під, з-за, із-за, з-поміж, з-понад).
     - Multi-word prepositional locutions (§ 42, п. 3: згідно з, відповідно до, під час, у зв'язку з).
     - Anti-calque & government norms (по vs о/з/за/на, завдяки vs через, протягом vs на протязі).
  2. Conjunctions (Сполучники):
     - Homophonous sequence disambiguation (§ 43, п. 1 та примітка: проте/зате vs про те/за те,
       щоб vs що б, якби vs як би, якщо vs як що).
     - Joining conjunctions (Академічна граматика; СУМ-20: також/теж vs так же/те ж).
     - Coordinating vs subordinating conjunction function.
  3. Particles (Частки):
     - Orthography of не and ні (§ 44, п. 1 окремо: з дієсловами, дієприслівниками, дієприкметниками
       з залежними словами, заперечення/протиставлення з «а»; § 44, п. 2 разом: якщо без «не» не вживається,
       якщо утворює єдине поняття, з одиничними дієприкметниками-означеннями).
     - Hyphenated and standalone enclitic particles (§ 44, п. 3.1: -бо, -но, -то, -от, -таки vs таки дійшов;
       § 44, п. 3.2: будь-, казна-, хтозна- vs будь у кого).

Provides targeted pedagogical feedback explaining the specific orthographic or syntactic rule,
and guarantees zero collisions among options.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FunctionWordCategory(StrEnum):
    """Specific categories of function words practice."""

    # Prepositions (Прийменники)
    PREPOSITION_HYPHENATED = "preposition_hyphenated"
    PREPOSITION_COMPOUND_SOLID = "preposition_compound_solid"
    PREPOSITION_LOCUTION_SEPARATE = "preposition_locution_separate"
    PREPOSITION_GOVERNMENT_PO = "preposition_government_po"
    PREPOSITION_ZAVDYAKY_VS_CHEREZ = "preposition_zavdyaky_vs_cherez"
    PREPOSITION_PROTYAHOM_VS_NA_PROTYAZI = "preposition_protyahom_vs_na_protyazi"

    # Conjunctions (Сполучники)
    CONJUNCTION_PROTE_ZATE = "conjunction_prote_zate"
    CONJUNCTION_SHCHOB = "conjunction_shchob"
    CONJUNCTION_YAKBY = "conjunction_yakby"
    CONJUNCTION_YAKSHCHO = "conjunction_yakshcho"
    CONJUNCTION_TAKOZH_TEZH = "conjunction_takozh_tezh"

    # Particles (Частки)
    PARTICLE_NE_SOLID = "particle_ne_solid"
    PARTICLE_NE_CONTRAST_SEPARATE = "particle_ne_contrast_separate"
    PARTICLE_NE_VERB_SEPARATE = "particle_ne_verb_separate"
    PARTICLE_NE_PARTICIPLE = "particle_ne_participle"
    PARTICLE_HYPHENATED_ENCLITICS = "particle_hyphenated_enclitics"
    PARTICLE_PREFIX_SPLIT = "particle_prefix_split"


class FunctionWordInterferenceType(StrEnum):
    """Taxonomy of grammatical, orthographic, and interference misconceptions."""

    MISSING_HYPHEN_PREPOSITION = "missing_hyphen_preposition"
    FALSE_SEPARATE_PREPOSITION = "false_separate_preposition"
    FALSE_SOLID_PREPOSITION = "false_solid_preposition"
    FALSE_HYPHEN_PREPOSITION = "false_hyphen_preposition"
    FALSE_SOLID_LOCUTION = "false_solid_locution"
    FALSE_HYPHEN_LOCUTION = "false_hyphen_locution"
    RUSSIAN_CALQUE_PO = "russian_calque_po"
    RUSSIAN_CALQUE_GENERAL = "russian_calque_general"
    LEXICAL_SEMANTIC_CONFUSION = "lexical_semantic_confusion"
    MISMATCHED_CAUSAL_CONSEQUENCE = "mismatched_causal_consequence"
    AIR_DRAFT_CALQUE_FOR_DURATION = "air_draft_calque_for_duration"
    HOMOPHONE_CONJUNCTION_FOR_PRONOUN = "homophone_conjunction_for_pronoun"
    HOMOPHONE_PRONOUN_FOR_CONJUNCTION = "homophone_pronoun_for_conjunction"
    HOMOPHONE_ADVERB_FOR_CONJUNCTION = "homophone_adverb_for_conjunction"
    FALSE_HYPHEN_CONJUNCTION = "false_hyphen_conjunction"
    FALSE_SOLID_NE_CONTRAST = "false_solid_ne_contrast"
    FALSE_SEPARATE_NE_VERB = "false_separate_ne_verb"
    FALSE_SEPARATE_NE_NOUN_ADJ = "false_separate_ne_noun_adj"
    FALSE_SOLID_NE_VERB = "false_solid_ne_verb"
    FALSE_SOLID_NE_PARTICIPLE_WITH_DEPENDENTS = "false_solid_ne_participle_with_dependents"
    FALSE_SEPARATE_NE_PARTICIPLE_ISOLATED = "false_separate_ne_participle_isolated"
    MISSING_HYPHEN_PARTICLE = "missing_hyphen_particle"
    FALSE_HYPHEN_PREPOSITIONAL_SPLIT = "false_hyphen_prepositional_split"
    FALSE_SOLID_PARTICLE = "false_solid_particle"
    FALSE_HYPHEN_PARTICLE = "false_hyphen_particle"
    FALSE_HYPHEN_INVERTED_TAKY = "false_hyphen_inverted_taky"


@dataclass(frozen=True)
class FunctionWordDistractor:
    """A distractor choice with error classification and bilingual explanation."""

    form: str
    interference_type: FunctionWordInterferenceType
    explanation_ua: str
    explanation_en: str


@dataclass(frozen=True)
class FunctionWordCard:
    """Practice card testing a function word rule with context and distractors."""

    card_id: str
    category: FunctionWordCategory
    cefr_level: str  # A1, A2, B1, B2
    sentence_before: str
    sentence_after: str
    correct_answer: str
    distractors: list[FunctionWordDistractor]
    rule_citation: str
    rule_summary_ua: str
    rule_summary_en: str

    @property
    def full_sentence(self) -> str:
        """Render the complete sentence with the correct answer."""
        sep_before = " " if self.sentence_before and not self.sentence_before.endswith(" ") else ""
        sep_after = " " if self.sentence_after and not self.sentence_after.startswith((" ", ",", ".", "!", "?", ":", ";")) else ""
        return f"{self.sentence_before}{sep_before}{self.correct_answer}{sep_after}{self.sentence_after}".strip()

    @property
    def prompt_display(self) -> str:
        """Render the sentence prompt with a blank indicator."""
        sep_before = " " if self.sentence_before and not self.sentence_before.endswith(" ") else ""
        sep_after = " " if self.sentence_after and not self.sentence_after.startswith((" ", ",", ".", "!", "?", ":", ";")) else ""
        return f"{self.sentence_before}{sep_before}_______{sep_after}{self.sentence_after}".strip()

    def all_options(self, seed: int | None = None) -> list[str]:
        """Return the shuffled list of all 4 unique options with balanced positioning."""
        opts = [self.correct_answer] + [d.form for d in self.distractors]
        if seed is not None:
            rnd = random.Random(seed)
        else:
            # Deterministic per-card seed derived from sha256(card_id) to ensure
            # well-balanced answer positions (0, 1, 2, 3) across the deck
            card_seed = int(hashlib.sha256(self.card_id.encode("utf-8")).hexdigest()[:8], 16)
            rnd = random.Random(card_seed)
        rnd.shuffle(opts)
        return opts


# ============================================================================
# Rule Definitions & Curated Canonical Instances
# ============================================================================

CANONICAL_PREPOSITION_HYPHENATED_ITEMS = [
    {
        "id": "prep_hyphen_z_pid_1",
        "category": FunctionWordCategory.PREPOSITION_HYPHENATED,
        "cefr": "A2",
        "before": "Кошеня визирнуло",
        "after": "дивана й злякано нявкнуло.",
        "correct": "з-під",
        "distractors": [
            ("зпід", FunctionWordInterferenceType.MISSING_HYPHEN_PREPOSITION, "Складні прийменники з першою частиною «з-», «із-» пишуться через дефіс, а не разом.", "Compound prepositions with z-/iz- are written with a hyphen, not as a single word."),
            ("з під", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Це складний просторовий прийменник, він пишеться через дефіс, а не двома окремими словами.", "This is a compound directional preposition written with a hyphen, not two separate words."),
            ("із під", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Складний прийменник пишеться через дефіс: «з-під» або «із-під», а не двома окремими словами.", "Compound preposition is written with a hyphen: 'з-під' or 'із-під', not two separate words."),
        ],
        "citation": "Правопис 2019, § 42, п. 2",
        "rule_ua": "Складні прийменники з початковими «з-», «із-» пишуться через дефіс: з-під, з-за, із-за, з-поміж, з-понад, з-посеред.",
        "rule_en": "Compound prepositions starting with z-/iz- are hyphenated: з-під, з-за, із-за, з-поміж, з-понад.",
    },
    {
        "id": "prep_hyphen_z_za_2",
        "category": FunctionWordCategory.PREPOSITION_HYPHENATED,
        "cefr": "A2",
        "before": "Сонце повільно випливало",
        "after": "густих ранкових хмар.",
        "correct": "з-за",
        "distractors": [
            ("зза", FunctionWordInterferenceType.MISSING_HYPHEN_PREPOSITION, "Прийменник «з-за» обов'язково пишеться через дефіс (Правопис 2019, § 42, п. 2).", "The preposition 'з-за' must be hyphenated."),
            ("з за", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Складний прийменник руху з протилежного боку пишеться через дефіс, а не окремо.", "Written with a hyphen, not as two separate words."),
            ("із за", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Обидві частини складного прийменника з'єднуються дефісом: «з-за» або «із-за».", "Both parts are connected with a hyphen."),
        ],
        "citation": "Правопис 2019, § 42, п. 2",
        "rule_ua": "Складні прийменники з початковими «з-», «із-» пишуться через дефіс: з-під, з-за, із-за, з-поміж.",
        "rule_en": "Compound prepositions starting with z-/iz- are hyphenated.",
    },
    {
        "id": "prep_hyphen_z_pomizh_3",
        "category": FunctionWordCategory.PREPOSITION_HYPHENATED,
        "cefr": "B1",
        "before": "Він вибрав найстигліше яблуко",
        "after": "усіх плодів у кошику.",
        "correct": "з-поміж",
        "distractors": [
            ("зпоміж", FunctionWordInterferenceType.MISSING_HYPHEN_PREPOSITION, "Прийменники з першою частиною «з-» пишуться через дефіс.", "Prepositions starting with z- require a hyphen."),
            ("з поміж", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "«З-поміж» є єдиним складним прийменником і пишеться через дефіс.", "Written as a single hyphenated preposition."),
            ("із поміж", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Обидві частини складного прийменника з'єднуються дефісом: «з-поміж» або «із-поміж», а не окремо.", "Both parts are connected with a hyphen: 'з-поміж' or 'із-поміж'."),
        ],
        "citation": "Правопис 2019, § 42, п. 2",
        "rule_ua": "Складні прийменники з «з-» пишуться через дефіс: з-поміж, з-понад, з-посеред.",
        "rule_en": "Compound prepositions with z- are written with a hyphen.",
    },
    {
        "id": "prep_hyphen_z_ponad_4",
        "category": FunctionWordCategory.PREPOSITION_HYPHENATED,
        "cefr": "B1",
        "before": "Місяць повільно піднявся",
        "after": "верхівок соснового лісу.",
        "correct": "з-понад",
        "distractors": [
            ("зпонад", FunctionWordInterferenceType.MISSING_HYPHEN_PREPOSITION, "Прийменник «з-понад» пишеться через дефіс.", "The preposition 'з-понад' is written with a hyphen."),
            ("з понад", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Складні прийменники з «з-» не пишуться окремо.", "Compound prepositions starting with z- are not written separately."),
            ("із понад", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Складні прийменники з початковою частиною «з-», «із-» пишуться через дефіс («з-понад», «із-понад»), а не окремими словами.", "Prepositions with z-/iz- are hyphenated, not written separately."),
        ],
        "citation": "Правопис 2019, § 42, п. 2",
        "rule_ua": "Складні прийменники з першою частиною «з-» пишуться через дефіс: з-понад.",
        "rule_en": "Compound prepositions with z- are written with a hyphen.",
    },
]

CANONICAL_PREPOSITION_COMPOUND_SOLID_ITEMS = [
    {
        "id": "prep_solid_posered_1",
        "category": FunctionWordCategory.PREPOSITION_COMPOUND_SOLID,
        "cefr": "A2",
        "before": "Маленька галявина розкинулася",
        "after": "густого соснового лісу.",
        "correct": "посеред",
        "distractors": [
            ("по серед", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Складний прийменник «посеред» утворений злиттям двох прийменників і пишеться разом.", "Compound preposition 'посеред' is written as a single word."),
            ("по-серед", FunctionWordInterferenceType.FALSE_HYPHEN_PREPOSITION, "Через дефіс пишуться лише прийменники з першою частиною «з-», а «посеред» пишеться разом.", "Only prepositions beginning with z-/iz- are hyphenated; 'посеред' is solid."),
            ("посеред-лісу", FunctionWordInterferenceType.FALSE_HYPHEN_LOCUTION, "Прийменник «посеред» пишеться окремим словом від наступного іменника.", "Preposition 'посеред' is written as a separate word before the noun."),
        ],
        "citation": "Правопис 2019, § 42, п. 1",
        "rule_ua": "Складні прийменники, утворені злиттям кількох прийменників або прийменника з іншою частиною мови, пишуться разом: посеред, задля, поміж, заради, внаслідок.",
        "rule_en": "Compound prepositions formed by joining prepositions or a preposition with another word are written solid: посеред, задля, поміж.",
    },
    {
        "id": "prep_solid_zadlya_2",
        "category": FunctionWordCategory.PREPOSITION_COMPOUND_SOLID,
        "cefr": "B1",
        "before": "Українці об'єдналися",
        "after": "перемоги та спільного майбутнього.",
        "correct": "задля",
        "distractors": [
            ("за для", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Складний прийменник мети «задля» пишеться разом (Правопис 2019, § 42, п. 1).", "Purpose preposition 'задля' is written as one word."),
            ("за-для", FunctionWordInterferenceType.FALSE_HYPHEN_PREPOSITION, "Дефіс вживається лише для прийменників із початковим «з-» (з-під, з-за). «Задля» пишеться разом.", "Hyphens are only used for z- prefixes; 'задля' is solid."),
            ("задля-того", FunctionWordInterferenceType.FALSE_HYPHEN_LOCUTION, "Прийменник «задля» не з'єднується дефісом з іншими словами.", "Preposition 'задля' is not hyphenated with other words."),
        ],
        "citation": "Правопис 2019, § 42, п. 1",
        "rule_ua": "Складні прийменники мети й причини пишуться разом: задля, заради, внаслідок.",
        "rule_en": "Compound prepositions of purpose and cause are written solid: задля, заради.",
    },
    {
        "id": "prep_solid_vnaslidok_3",
        "category": FunctionWordCategory.PREPOSITION_COMPOUND_SOLID,
        "cefr": "B2",
        "before": "Рух поїздів затримано",
        "after": "несприятливих погодних умов.",
        "correct": "внаслідок",
        "distractors": [
            ("в наслідок", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "У ролі прийменника причини («через щось») «внаслідок» пишеться разом. Окремо пишеться іменник із прийменником: «вірити в наслідок справи».", "As a preposition meaning 'as a consequence of', 'внаслідок' is solid. Separate 'в наслідок' is a noun with preposition."),
            ("в-наслідок", FunctionWordInterferenceType.FALSE_HYPHEN_PREPOSITION, "Складні прийменники такого типу пишуться разом, без дефіса.", "Written solid without a hyphen."),
            ("у-наслідок", FunctionWordInterferenceType.FALSE_HYPHEN_PREPOSITION, "Складний прийменник «унаслідок» пишеться разом без дефіса.", "Written solid without a hyphen."),
        ],
        "citation": "Правопис 2019, § 42, п. 1",
        "rule_ua": "Прийменники, утворені з прийменника та іменника, пишуться разом: внаслідок, напередодні, упродовж.",
        "rule_en": "Prepositions formed from a preposition and a noun are written solid: внаслідок, напередодні.",
    },
    {
        "id": "prep_solid_naperedodni_4",
        "category": FunctionWordCategory.PREPOSITION_COMPOUND_SOLID,
        "cefr": "B1",
        "before": "Ми зібралися родиною",
        "after": "Різдва Христового.",
        "correct": "напередодні",
        "distractors": [
            ("на передодні", FunctionWordInterferenceType.FALSE_SEPARATE_PREPOSITION, "Прийменник часового значення «напередодні» пишеться разом.", "Temporal preposition 'напередодні' is written solid."),
            ("на-передодні", FunctionWordInterferenceType.FALSE_HYPHEN_PREPOSITION, "Складні прийменники без частки «з-» пишуться разом, дефіс не вживається.", "No hyphen is used; written solid."),
            ("напередодні-свята", FunctionWordInterferenceType.FALSE_HYPHEN_LOCUTION, "Прийменник «напередодні» пишеться окремим словом від наступного іменника.", "Preposition is written separately from the following noun."),
        ],
        "citation": "Правопис 2019, § 42, п. 1",
        "rule_ua": "Прийменники, утворені злиттям прийменників та іменників, пишуться разом: напередодні, внаслідок, упродовж.",
        "rule_en": "Prepositions formed from prepositions and nouns are written solid: напередодні.",
    },
]

CANONICAL_PREPOSITION_LOCUTIONS_ITEMS = [
    {
        "id": "prep_loc_zhidno_z_1",
        "category": FunctionWordCategory.PREPOSITION_LOCUTION_SEPARATE,
        "cefr": "A2",
        "before": "Усі документи складено",
        "after": "встановленими державними нормами.",
        "correct": "згідно з",
        "distractors": [
            ("згідноз", FunctionWordInterferenceType.FALSE_SOLID_LOCUTION, "Прийменникові сполуки пишуться окремими словами: «згідно з».", "Prepositional locutions are written as separate words: 'згідно з'."),
            ("згідно-з", FunctionWordInterferenceType.FALSE_HYPHEN_LOCUTION, "Прийменникова сполука «згідно з» пишеться окремо без дефіса.", "Written as separate words without a hyphen."),
            ("згідно до", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Нормативна українська конструкція: «згідно з» (+ орудний відмінок) або «відповідно до» (+ родовий відмінок).", "Standard Ukrainian construction is 'згідно з' (+ instrumental) or 'відповідно до' (+ genitive)."),
        ],
        "citation": "Правопис 2019, § 42, п. 3; Культура мови",
        "rule_ua": "Прийменникові сполуки пишуться окремо: згідно з, відповідно до, під час, у разі, залежно від.",
        "rule_en": "Prepositional locutions are written as separate words: згідно з, відповідно до, під час.",
    },
    {
        "id": "prep_loc_vidpovidno_do_2",
        "category": FunctionWordCategory.PREPOSITION_LOCUTION_SEPARATE,
        "cefr": "B1",
        "before": "Рішення ухвалено",
        "after": "чинного законодавства України.",
        "correct": "відповідно до",
        "distractors": [
            ("відповіднодо", FunctionWordInterferenceType.FALSE_SOLID_LOCUTION, "Прийменникова сполука «відповідно до» пишеться двома окремими словами.", "Written as two separate words: 'відповідно до'."),
            ("відповідно з", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Нормативно вживати «відповідно до» (+ родовий відмінок) або «згідно з» (+ орудний відмінок). Конструкція «відповідно з» є калькою.", "Standard form is 'відповідно до' (+ Genitive) or 'згідно з' (+ Instrumental)."),
            ("у відповідності до", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Конструкція «у відповідності до» є канцеляристською калькою; нормативний варіант — «відповідно до».", "Standard natural Ukrainian is 'відповідно до' rather than the calque 'у відповідності до'."),
        ],
        "citation": "Правопис 2019, § 42, п. 3; СУМ-20",
        "rule_ua": "Прийменникові сполуки пишуться окремо: відповідно до, згідно з.",
        "rule_en": "Prepositional locutions are written as separate words: відповідно до.",
    },
    {
        "id": "prep_loc_pid_chas_3",
        "category": FunctionWordCategory.PREPOSITION_LOCUTION_SEPARATE,
        "cefr": "A2",
        "before": "Слухачі вимкнули телефони",
        "after": "важливої лекції.",
        "correct": "під час",
        "distractors": [
            ("підчас", FunctionWordInterferenceType.FALSE_SOLID_LOCUTION, "Прийменникова сполука «під час» завжди пишеться двома окремими словами.", "Prepositional locution 'під час' is always two separate words."),
            ("під-час", FunctionWordInterferenceType.FALSE_HYPHEN_LOCUTION, "Дефіс у сполуці «під час» не вживається.", "No hyphen is used in 'під час'."),
            ("во врем'я", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Суржикове запозичення; нормативний український вислів — «під час».", "Surzhyk borrowing; correct Ukrainian form is 'під час'."),
        ],
        "citation": "Правопис 2019, § 42, п. 3",
        "rule_ua": "Прийменникові сполуки пишуться окремими словами: під час, у разі, у зв'язку з.",
        "rule_en": "Prepositional locutions are written separately: під час.",
    },
]

CANONICAL_PREPOSITION_GOVERNMENT_ITEMS = [
    {
        "id": "prep_gov_po_chas_1",
        "category": FunctionWordCategory.PREPOSITION_GOVERNMENT_PO,
        "cefr": "A2",
        "before": "Потяг вирушає рівно",
        "after": "сьомій годині вечора.",
        "correct": "о",
        "distractors": [
            ("по", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Прийменник «по» з місцевим відмінком означає «після» («по сьомій» = після сьомої години), а не точний час настання події («о сьомій»).", "Preposition 'по' + locative means 'after' ('по сьомій' = after seven), not exact time ('о сьомій')."),
            ("в", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Конструкція «в сім годин» — калька з російської; українською мовою на позначення точного часу кажемо: «о сьомій годині» (прийменник «о / об» із порядковим числівником).", "Construction 'в сім годин' is a Russian calque; Ukrainian marks exact time with 'о / об' and ordinal numeral: 'о сьомій годині'."),
            ("біля", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Прийменник «біля» вказує на просторову близькість (біля столу), а для приблизного часу вживають «близько» (близько сьомої); для точного ж часу потрібен прийменник «о» (о сьомій).", "Preposition 'біля' indicates spatial proximity, while approximate time uses 'близько'; exact time requires 'о / об'."),
        ],
        "citation": "Антоненко-Давидович «Як ми говоримо»; СУМ-20",
        "rule_ua": "На позначення точного часу вживаємо прийменники «о», «об» («о котрій годині? — о сьомій»), а не «по» чи «в».",
        "rule_en": "To state time, Ukrainian uses 'о / об' ('о сьомій годині'), not 'по' or 'в'.",
    },
    {
        "id": "prep_gov_po_predmet_2",
        "category": FunctionWordCategory.PREPOSITION_GOVERNMENT_PO,
        "cefr": "B1",
        "before": "Студенти успішно склали іспит",
        "after": "української літератури.",
        "correct": "з",
        "distractors": [
            ("по", FunctionWordInterferenceType.RUSSIAN_CALQUE_PO, "Назву предмета, дисципліни чи галузі передаємо прийменником «з» («іспит з літератури»), а не калькованим «по літературі».", "Use preposition 'з' for subjects and disciplines ('іспит з літератури'), avoiding calque 'по'."),
            ("по темі", FunctionWordInterferenceType.RUSSIAN_CALQUE_PO, "«Іспит з предмета» — усталена синтаксична норма української мови.", "Standard Ukrainian syntax requires 'з' + Genitive for academic subjects."),
            ("про", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Прийменник «про» вказує на зміст розмови чи розповіді, а назва іспиту керується прийменником «з».", "Use 'з' for academic examinations."),
        ],
        "citation": "Антоненко-Давидович «Як ми говоримо»; Словник труднощів",
        "rule_ua": "Навчальні дисципліни та галузі знань вимагають прийменника «з» (з математики, з історії), а не «по».",
        "rule_en": "Academic subjects take preposition 'з' with Genitive (іспит з історії), not 'по'.",
    },
    {
        "id": "prep_gov_po_zasib_3",
        "category": FunctionWordCategory.PREPOSITION_GOVERNMENT_PO,
        "cefr": "A2",
        "before": "Він вирішив звільнитися",
        "after": "і знайти нову роботу.",
        "correct": "за власним бажанням",
        "distractors": [
            ("по власному бажанню", FunctionWordInterferenceType.RUSSIAN_CALQUE_PO, "Конструкція «по власному бажанню» — калька з російської («по собственному желанию»). В українській мові вживаємо «за власним бажанням».", "Construction 'по власному бажанню' is a Russian calque ('по собственному желанию'); standard Ukrainian uses 'за власним бажанням'."),
            ("через власне бажання", FunctionWordInterferenceType.MISMATCHED_CAUSAL_CONSEQUENCE, "Прийменник «через» позначає несприятливу причину чи перешкоду (через хворобу, через негоду). Для свідомого вибору чи мотивації вживаємо «за власним бажанням».", "Preposition 'через' indicates an adverse cause or obstacle; for intentional choice or motivation, use 'за власним бажанням'."),
            ("при власному бажанні", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Конструкція «при бажанні» — синтаксична калька російського «при желании». Нормативний літературний вислів — «за власним бажанням» (або «якщо є бажання / маючи бажання»).", "Phrase 'при власному бажанні' is a calque from Russian 'при желании'; standard Ukrainian uses 'за власним бажанням'."),
        ],
        "citation": "Антоненко-Давидович «Як ми говоримо»; СУМ-20",
        "rule_ua": "У значенні підстави або відповідності вживаємо прийменник «за» («за власним бажанням», «за наказом», «за правилами»), уникаючи російського калькованого «по».",
        "rule_en": "Ukrainian uses preposition 'за' for motivation or conformity ('за власним бажанням', 'за наказом'), not Russian calque 'по'.",
    },
    {
        "id": "prep_gov_zavdyaky_cherez_4",
        "category": FunctionWordCategory.PREPOSITION_ZAVDYAKY_VS_CHEREZ,
        "cefr": "B1",
        "before": "Матч довелося скасувати",
        "after": "сильну зливу та грозу.",
        "correct": "через",
        "distractors": [
            ("завдяки", FunctionWordInterferenceType.MISMATCHED_CAUSAL_CONSEQUENCE, "«Завдяки» вживається лише тоді, коли наслідок позитивний (завдяки допомозі). Для негативних чи несприятливих обставин вживаємо «через».", "'Завдяки' is used only for positive causes. For adverse or negative causes, use 'через'."),
            ("по причині", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "«По причині» — груба російська калька (рос. «по причине»). Нормативний прийменник — «через».", "Calque from Russian 'по причине'; use Ukrainian 'через'."),
            ("із-за", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Прийменник «із-за» в літературній мові позначає просторовий рух звідкись («вийти із-за столу»), а причинне значення є ненормативним суржиком.", "Literary 'із-за' denotes spatial origin ('вийти із-за столу'); causal use is substandard."),
        ],
        "citation": "Антоненко-Давидович «Як ми говоримо»; Культура слова",
        "rule_ua": "«Завдяки» вживаємо тільки при позитивних наслідках (+ давальний в.); якщо наслідок негативний або нейтральний — вживаємо «через» (+ знахідний в.).",
        "rule_en": "'Завдяки' (+ Dative) is reserved for positive factors; use 'через' (+ Accusative) for negative or neutral causes.",
    },
    {
        "id": "prep_gov_protyahom_5",
        "category": FunctionWordCategory.PREPOSITION_PROTYAHOM_VS_NA_PROTYAZI,
        "cefr": "B1",
        "before": "Команда наполегливо тренувалася",
        "after": "усього навчального року.",
        "correct": "протягом",
        "distractors": [
            ("на протязі", FunctionWordInterferenceType.AIR_DRAFT_CALQUE_FOR_DURATION, "«На протязі» означає перебування на струмені повітря («стояти на протязі»). На позначення часової тривалості слід вживати «протягом» або «упродовж».", "'На протязі' literally means in an air draft. For time duration, use 'протягом' or 'упродовж'."),
            ("у протязі", FunctionWordInterferenceType.AIR_DRAFT_CALQUE_FOR_DURATION, "В українській мові немає прийменника «у протязі»; нормативними є «протягом» або «упродовж».", "Standard temporal prepositions are 'протягом' or 'упродовж'."),
            ("в протязі", FunctionWordInterferenceType.AIR_DRAFT_CALQUE_FOR_DURATION, "Калька російського виразу; на позначення тривалості в часі вживаємо «протягом» або «упродовж».", "Calque; use 'протягом' or 'упродовж'."),
        ],
        "citation": "Антоненко-Давидович «Як ми говоримо»",
        "rule_ua": "На позначення тривалості в часі вживаємо «протягом» або «упродовж». Вислів «на протязі» вживається лише у значенні різкого струменя повітря між дверима чи вікнами.",
        "rule_en": "Use 'протягом' or 'упродовж' for time duration. 'На протязі' refers solely to an air draft.",
    },
]

CANONICAL_CONJUNCTION_ITEMS = [
    {
        "id": "conj_prote_zate_1",
        "category": FunctionWordCategory.CONJUNCTION_PROTE_ZATE,
        "cefr": "B1",
        "before": "Завдання було складним,",
        "after": "ми розв'язали його вчасно.",
        "correct": "проте",
        "distractors": [
            ("про те", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "«Проте» є протиставним сполучником (= «але») і пишеться разом. Окремо «про те» пишеться тоді, коли це прийменник із займенником («ми говорили про те диво»).", "'Проте' is an adversative conjunction (= 'але') written solid. Separate 'про те' is preposition + pronoun."),
            ("про-те", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Сполучник «проте» пишеться разом, без дефіса.", "Conjunction 'проте' is written solid without a hyphen."),
            ("за це", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Для протиставлення двох частин речення вживаємо сполучник «проте» або «зате».", "Use conjunction 'проте' or 'зате' for sentence contrast."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Сполучники «проте», «зате» (= але, однак) пишуться разом. Їх слід відрізняти від прийменників із вказівним займенником «про те», «за те», які пишуться окремо.",
        "rule_en": "Conjunctions 'проте', 'зате' (= but, however) are written solid, unlike preposition + pronoun 'про те', 'за те'.",
    },
    {
        "id": "conj_pro_te_pronoun_2",
        "category": FunctionWordCategory.CONJUNCTION_PROTE_ZATE,
        "cefr": "B1",
        "before": "Учитель детально розповів",
        "after": "як відбувалися визвольні змагання.",
        "correct": "про те,",
        "distractors": [
            ("проте,", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Тут «те» — вказівний займенник із прийменником «про» («розповів про що? — про те»). Тому пишемо окремо: «про те».", "Here 'те' is a demonstrative pronoun with preposition 'про'; written separately as 'про те'."),
            ("про-те,", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Прийменник із займенником пишеться окремо, без дефіса.", "Preposition with pronoun is written as two separate words."),
            ("про шо,", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Форма «шо» є грубим просторіччям; нормативна літературна мова вимагає «про те, що...».", "Substandard form; literary Ukrainian uses 'про те, що'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Прийменник із займенником «про те» пишеться окремо, якщо до слова «те» можна поставити запитання (про що? — про те).",
        "rule_en": "Preposition + pronoun 'про те' is written separately when 'те' answers a case question (about what? -> about that).",
    },
    {
        "id": "conj_shchob_3",
        "category": FunctionWordCategory.CONJUNCTION_SHCHOB,
        "cefr": "A2",
        "before": "Він прийшов раніше,",
        "after": "допомогти вчителю підготувати клас.",
        "correct": "щоб",
        "distractors": [
            ("що б", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Сполучник мети «щоб» пишеться разом. Частку «б» тут не можна відкинути чи переставити («Він прийшов раніше, що допомогти» ❌).", "Purpose conjunction 'щоб' is written solid. The particle 'б' cannot be removed without ruining the sentence."),
            ("що-б", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Сполучник «щоб» пишеться разом, дефіс не вживається.", "Conjunction 'щоб' is written solid without a hyphen."),
            ("що", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Сполучник мети «щоб» не можна замінити простим «що» без втрати цільового значення.", "Purpose clause requires 'щоб', not bare 'що'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Сполучник мети та з'ясувальний «щоб» пишеться разом. Займенник із часткою «що б» пишеться окремо (частку «б» можна переставити).",
        "rule_en": "Purpose conjunction 'щоб' is written solid. Relative pronoun with particle 'що б' is written separately.",
    },
    {
        "id": "conj_shcho_b_pronoun_4",
        "category": FunctionWordCategory.CONJUNCTION_SHCHOB,
        "cefr": "B1",
        "before": "Цікаво,",
        "after": "ти сказав на моєму місці?",
        "correct": "що б",
        "distractors": [
            ("щоб", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Тут «що» — питальний займенник, а «б» — умовна частка, яку можна переставити («Що ти сказав би?»). Тому пишемо окремо: «що б».", "Here 'що' is an interrogative pronoun and 'б' is a moveable conditional particle ('Що ти сказав би?'); written separately."),
            ("що-б", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Займенник із часткою пишеться окремо, без дефіса.", "Pronoun with particle is written separately without a hyphen."),
            ("якби", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "«Якби» є умовним сполучником («якби знав»), а в цьому реченні потрібен займенник «що» з часткою «б».", "'Якби' is a conditional conjunction; here the question requires pronoun 'що' + particle 'б'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Займенник «що» з часткою «б» пишеться окремо, якщо частку «б» можна вилучити або переставити в інше місце речення.",
        "rule_en": "Pronoun 'що' with particle 'б' is written separately if 'б' can be moved elsewhere in the clause.",
    },
    {
        "id": "conj_yakby_5",
        "category": FunctionWordCategory.CONJUNCTION_YAKBY,
        "cefr": "B1",
        "before": "Ми встигли б на поїзд,",
        "after": "виїхали на пів години раніше.",
        "correct": "якби",
        "distractors": [
            ("як би", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Умовний сполучник «якби» (= «якщо б») пишеться разом.", "Conditional conjunction 'якби' (= 'if') is written solid."),
            ("як-би", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Сполучник «якби» пишеться разом, без дефіса.", "Written solid without a hyphen."),
            ("єсли б", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "«Єсли б» — ненормативний суржик. Літературний умовний сполучник — «якби».", "Substandard surzhyk; standard conditional conjunction is 'якби'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Умовний сполучник «якби» (= якщо б) пишеться разом. Прислівник «як» із часткою «би» пишеться окремо: «Як би ти це зробив?»",
        "rule_en": "Conditional conjunction 'якби' (= if) is solid. Adverb of manner 'як' + particle 'би' is written separately.",
    },
    {
        "id": "conj_yak_by_adverb_6",
        "category": FunctionWordCategory.CONJUNCTION_YAKBY,
        "cefr": "B2",
        "before": "Не знаю,",
        "after": "точніше сформулювати цю думку.",
        "correct": "як би",
        "distractors": [
            ("якби", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Тут «як» — прислівник способу дії («яким чином»), а «би» — частка. Їх пишемо окремо: «як би».", "Here 'як' is an adverb of manner ('in what way') and 'би' is a particle; written separately as 'як би'."),
            ("як-би", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Прислівник із часткою пишеться двома окремими словами.", "Written as two separate words without a hyphen."),
            ("аби", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "«Аби» має значення «лише б» або «щоб», що спотворює зміст цього речення.", "'Аби' alters the intended meaning of manner."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Прислівник «як» із часткою «би» пишеться окремо, якщо частку можна переставити («Як точніше б сформулювати цю думку»).",
        "rule_en": "Adverb 'як' with particle 'би' is written separately when expressing manner.",
    },
    {
        "id": "conj_takozh_7",
        "category": FunctionWordCategory.CONJUNCTION_TAKOZH_TEZH,
        "cefr": "A2",
        "before": "Моя сестра вивчає іноземні мови, і я",
        "after": "вирішив обрати філологічний факультет.",
        "correct": "також",
        "distractors": [
            ("так же", FunctionWordInterferenceType.HOMOPHONE_ADVERB_FOR_CONJUNCTION, "«Так же» є поєднанням прислівника «так» із часткою «же» («зроби так же»). Для зв'язку речень вживаємо сполучники «також», «теж».", "'Так же' is adverb + particle ('in the same way'). To join clauses, use conjunctions 'також', 'теж'."),
            ("тоже", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Слово «тоже» — грубий русизм. В українській мові слід уживати «також» або «теж».", "'Тоже' is a Russianism; use Ukrainian 'також' or 'теж'."),
            ("так-же", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "В українській мові немає написання «так-же».", "No such hyphenated form exists in Ukrainian."),
        ],
        "citation": "Правопис 2019, § 43, п. 1; Академічна граматика; СУМ-20",
        "rule_ua": "Сполучники «також», «теж» пишуться разом. Слід уникати русизму «тоже». Сполука «так же» пишеться окремо, коли «так» — прислівник.",
        "rule_en": "Conjunctions 'також', 'теж' are written solid. Avoid Russianism 'тоже'.",
    },
    {
        "id": "conj_yakshcho_8",
        "category": FunctionWordCategory.CONJUNCTION_YAKSHCHO,
        "cefr": "A2",
        "before": "Ми обов'язково підемо на прогулянку,",
        "after": "до вечора вигляне сонце.",
        "correct": "якщо",
        "distractors": [
            ("як що", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Умовний сполучник «якщо» пишеться разом. Окремо «як що» пишеться лише тоді, коли «що» є окремим займенником.", "Conditional conjunction 'якщо' is written solid."),
            ("як-що", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Сполучник «якщо» пишеться разом, без дефіса.", "Written solid without a hyphen."),
            ("єслі", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Слово «єслі» — ненормативний суржик. В українській мові вживаємо сполучник «якщо» або «якби».", "Substandard Surzhyk; use Ukrainian 'якщо'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Умовний сполучник «якщо» пишеться разом.",
        "rule_en": "Conditional conjunction 'якщо' is written solid.",
    },
    {
        "id": "conj_yak_shcho_pronoun_9",
        "category": FunctionWordCategory.CONJUNCTION_YAKSHCHO,
        "cefr": "B1",
        "before": "Дідусь терпляче навчив онука,",
        "after": "лагодити в хаті.",
        "correct": "як що",
        "distractors": [
            ("якщо", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Тут «як» (прислівник «як саме») та «що» (займенник-додаток «що саме») є самостійними словами: «як що лагодити» (тобто як лагодити яку річ). Умовний сполучник «якщо» тут неможливий.", "Here 'як' (adverb 'how') and 'що' (pronoun 'what') are independent words in an indirect clause ('how to fix what'). Conditional 'якщо' is ungrammatical here."),
            ("як-що", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Прислівник із займенником пишуться окремо без дефіса.", "Adverb with pronoun is written as two separate words without a hyphen."),
            ("якби", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Сполучник «якби» вимагає умовного способу й не поєднується з інфінітивом у з'ясувальному значенні.", "Conjunction 'якби' is conditional and incompatible with this structure."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Прислівник «як» із займенником «що» пишуться окремо, коли кожне слово має самостійне значення й відповідає на окреме питання.",
        "rule_en": "Adverb 'як' and pronoun 'що' are written separately when each preserves independent syntactic function.",
    },
    {
        "id": "conj_zate_10",
        "category": FunctionWordCategory.CONJUNCTION_PROTE_ZATE,
        "cefr": "B1",
        "before": "Ця квартира невелика,",
        "after": "дуже світла й затишна.",
        "correct": "зате",
        "distractors": [
            ("за те", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Протиставний сполучник «зате» (= але) пишеться разом.", "Adversative conjunction 'зате' (= but) is written solid."),
            ("за-те", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Сполучник «зате» пишеться разом, без дефіса.", "Conjunction 'зате' is written solid."),
            ("взамін", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Для протиставлення використовуємо сполучник «зате» або «проте».", "Use conjunction 'зате' or 'проте'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Протиставний сполучник «зате» пишеться разом.",
        "rule_en": "Adversative conjunction 'зате' is written solid.",
    },
    {
        "id": "conj_za_te_pronoun_11",
        "category": FunctionWordCategory.CONJUNCTION_PROTE_ZATE,
        "cefr": "B1",
        "before": "Я щиро дякую тобі",
        "after": "що ти завжди приходиш на допомогу.",
        "correct": "за те,",
        "distractors": [
            ("зате,", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Тут «те» — займенник із прийменником «за» (дякую за що? — за те). Пишеться окремо.", "Here 'те' is a pronoun with preposition 'за' (thank for what? -> for that). Written separately."),
            ("за-те,", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Прийменник із займенником пишеться окремо без дефіса.", "Preposition with pronoun is written separately."),
            ("за шо,", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Форма «шо» є грубим просторіччям.", "Substandard form; use standard 'за те, що'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1 та примітка",
        "rule_ua": "Прийменник із займенником «за те» пишеться окремо, якщо «те» відповідає на питання відмінка.",
        "rule_en": "Preposition with pronoun 'за те' is written separately when answering a case question.",
    },
    {
        "id": "conj_tezh_12",
        "category": FunctionWordCategory.CONJUNCTION_TAKOZH_TEZH,
        "cefr": "A2",
        "before": "Мої друзі вирушили в Карпати, і я",
        "after": "поїхав разом із ними.",
        "correct": "теж",
        "distractors": [
            ("те ж", FunctionWordInterferenceType.HOMOPHONE_PRONOUN_FOR_CONJUNCTION, "Приєднувальний сполучник «теж» (= також) пишеться разом. Окремо «те ж» пишеться лише тоді, коли «те» — займенник, а «ж» — частка («те ж саме»).", "Joining conjunction 'теж' is written solid. Separate 'те ж' is pronoun + particle."),
            ("те-ж", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Сполучник «теж» пишеться разом, без дефіса.", "Conjunction 'теж' is written solid."),
            ("тоже", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Слово «тоже» — русизм; нормативні форми — «теж» або «також».", "'Тоже' is a Russianism; use Ukrainian 'теж' or 'також'."),
        ],
        "citation": "Правопис 2019, § 43, п. 1; Академічна граматика; СУМ-20",
        "rule_ua": "Сполучник «теж» пишеться разом.",
        "rule_en": "Conjunction 'теж' is written solid.",
    },
    {
        "id": "conj_te_zh_pronoun_13",
        "category": FunctionWordCategory.CONJUNCTION_TAKOZH_TEZH,
        "cefr": "B1",
        "before": "Студент знову дав",
        "after": "саме формулювання, що й минулого разу.",
        "correct": "те ж",
        "distractors": [
            ("теж", FunctionWordInterferenceType.HOMOPHONE_CONJUNCTION_FOR_PRONOUN, "Тут «те» — вказівний займенник, а «ж» — підсилювальна частка, яку можна вилучити («дав те саме формулювання»). Пишеться окремо.", "Here 'те' is a demonstrative pronoun and 'ж' is an emphasizing particle that can be omitted; written separately."),
            ("те-ж", FunctionWordInterferenceType.FALSE_HYPHEN_CONJUNCTION, "Займенник із часткою пишеться окремо без дефіса.", "Pronoun with particle is written separately."),
            ("тоже", FunctionWordInterferenceType.RUSSIAN_CALQUE_GENERAL, "Русизм; вживаємо «те ж саме».", "Russianism; use 'те ж саме'."),
        ],
        "citation": "Правопис 2019, § 44, п. 1.13; СУМ-20",
        "rule_ua": "Вказівний займенник «те» з часткою «ж» пишеться окремо.",
        "rule_en": "Demonstrative pronoun 'те' with particle 'ж' is written separately.",
    },
]

CANONICAL_PARTICLE_ITEMS = [
    {
        "id": "part_ne_noun_solid_1",
        "category": FunctionWordCategory.PARTICLE_NE_SOLID,
        "cefr": "A2",
        "before": "Сказана ним",
        "after": "дуже засмутила щирих друзів.",
        "correct": "неправда",
        "distractors": [
            ("не правда", FunctionWordInterferenceType.FALSE_SEPARATE_NE_NOUN_ADJ, "«Неправда» пишеться разом, бо утворює нове поняття, яке можна замінити синонімом без «не» («брехня»). Окремо пишеться лише при прямому протиставленні («не правда, а брехня»).", "'Неправда' is written solid because it creates a new concept replaceable by synonym 'брехня'. Separate only with contrast."),
            ("не-правда", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Частка «не» з іменниками через дефіс не пишеться.", "The particle 'не' is never hyphenated with nouns."),
            ("ніправда", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Префікс заперечення понять — «не-», а не «ні-».", "The prefix for nouns is 'не-', not 'ні-'."),
        ],
        "citation": "Правопис 2019, § 44, п. 2.7",
        "rule_ua": "Частка «не» з іменниками, прикметниками та прислівниками пишеться разом, якщо слово у сполученні з «не» утворює нове поняття (можна замінити синонімом: неправда — брехня).",
        "rule_en": "Particle 'не' is solid with nouns, adjectives, and adverbs when forming a new concept replaceable by a synonym.",
    },
    {
        "id": "part_ne_contrast_sep_2",
        "category": FunctionWordCategory.PARTICLE_NE_CONTRAST_SEPARATE,
        "cefr": "A2",
        "before": "Річка біля нашого села була",
        "after": ", а зовсім мілка.",
        "correct": "не глибока",
        "distractors": [
            ("неглибока", FunctionWordInterferenceType.FALSE_SOLID_NE_CONTRAST, "Якщо є пряме протиставлення зі сполучником «а», частка «не» пишеться окремо від прикметника: «не глибока, а мілка».", "When there is explicit contrast with 'а', 'не' is written separately from the adjective."),
            ("не-глибока", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Частка «не» з прикметниками через дефіс не пишеться.", "Written as separate words without a hyphen."),
            ("ні глибока", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Для заперечення ознаки перед прикметником уживаємо частку «не», а не «ні».", "Use negative particle 'не' rather than 'ні'."),
        ],
        "citation": "Правопис 2019, § 44, п. 1.4",
        "rule_ua": "Частка «не» пишеться окремо, якщо в реченні є протиставлення зі сполучником «а», що заперечує ознаку: не глибокий, а мілкий; не правда, а брехня.",
        "rule_en": "Particle 'не' is written separately when there is explicit contrast with 'а' that negates the property.",
    },
    {
        "id": "part_ne_verb_sep_3",
        "category": FunctionWordCategory.PARTICLE_NE_VERB_SEPARATE,
        "cefr": "A1",
        "before": "Вибачте, я ще",
        "after": "цього простого правила.",
        "correct": "не знаю",
        "distractors": [
            ("незнаю", FunctionWordInterferenceType.FALSE_SOLID_NE_VERB, "Частка «не» з дієсловами завжди пишеться окремо (крім винятків, коли слово без «не» не вживається: ненавидіти, нехтувати).", "Particle 'не' is written separately with verbs (except when the verb cannot stand alone)."),
            ("не-знаю", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Частка «не» з дієсловами через дефіс не пишеться.", "Particle 'не' is never hyphenated with verbs."),
            ("ні знаю", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Для заперечення дії з дієсловами вживаємо частку «не», а не «ні».", "Verbs take negative particle 'не', not 'ні'."),
        ],
        "citation": "Правопис 2019, § 44, п. 1.1",
        "rule_ua": "Частка «не» з дієсловами та дієприслівниками пишеться окремо: не знаю, не бачив, не поспішаючи. Разом пишеться лише тоді, коли дієслово без «не» не вживається: ненавидіти, неволити, нехтувати.",
        "rule_en": "Particle 'не' is written separately with verbs and gerunds unless the verb cannot exist without 'не'.",
    },
    {
        "id": "part_ne_verb_solid_exception_4",
        "category": FunctionWordCategory.PARTICLE_NE_VERB_SEPARATE,
        "cefr": "B1",
        "before": "Справжній патріот завжди буде",
        "after": "будь-які прояви несправедливості та зради.",
        "correct": "ненавидіти",
        "distractors": [
            ("не навидіти", FunctionWordInterferenceType.FALSE_SEPARATE_NE_VERB, "Дієслово «ненавидіти» без «не» в сучасній українській мові не вживається, тому пишеться разом.", "The verb 'ненавидіти' cannot stand without 'не', so it is written solid."),
            ("не-навидіти", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Префікс «не-» у корені дієслова пишеться разом без дефіса.", "Written solid without a hyphen."),
            ("нінавидіти", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Слово починається з префікса «не-», а не «ні-».", "Prefix is 'не-', not 'ні-'."),
        ],
        "citation": "Правопис 2019, § 44, п. 2.5",
        "rule_ua": "Дієслова, які без «не» не вживаються, пишуться разом: ненавидіти, неволити, нехтувати, незчутися.",
        "rule_en": "Verbs that cannot be used without 'не' are written solid: ненавидіти, нехтувати.",
    },
    {
        "id": "part_ne_participle_solid_5",
        "category": FunctionWordCategory.PARTICLE_NE_PARTICIPLE,
        "cefr": "B2",
        "before": "На письмовому столі лежав",
        "after": "довгий лист від давнього друга.",
        "correct": "непрочитаний",
        "distractors": [
            ("не прочитаний", FunctionWordInterferenceType.FALSE_SEPARATE_NE_PARTICIPLE_ISOLATED, "Одиничний дієприкметник, який не має при собі пояснювальних (залежних) слів і виступає означенням, пишеться з «не» разом.", "An isolated participle without dependent words functioning as an attribute is written solid with 'не'."),
            ("не-прочитаний", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Дієприкметники з «не» пишуться разом без дефіса.", "Participles with 'не' are written solid, not hyphenated."),
            ("ні прочитаний", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Префікс заперечення прикметникових форм — «не-», а не «ні-».", "Prefix is 'не-', not 'ні-'."),
        ],
        "citation": "Правопис 2019, § 44, п. 2.8",
        "rule_ua": "Дієприкметник із «не» пишеться разом, якщо він є означенням і не має при собі залежних слів: непрочитаний лист, незасіяне поле.",
        "rule_en": "A participle is written solid with 'не' when acting as an attribute without dependent words.",
    },
    {
        "id": "part_ne_participle_sep_with_dep_6",
        "category": FunctionWordCategory.PARTICLE_NE_PARTICIPLE,
        "cefr": "B2",
        "before": "На столі лежав лист, ще",
        "after": "жодним із присутніх у кімнаті.",
        "correct": "не прочитаний",
        "distractors": [
            ("непрочитаний", FunctionWordInterferenceType.FALSE_SOLID_NE_PARTICIPLE_WITH_DEPENDENTS, "Якщо дієприкметник має залежні слова («ще не прочитаний жодним»), частка «не» пишеться окремо.", "If a participle has dependent words ('ще не прочитаний жодним'), 'не' is written separately."),
            ("не-прочитаний", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Дієприкметник із часткою «не» пишеться двома окремими словами, дефіс не вживається.", "Written as separate words without a hyphen."),
            ("ні прочитаний", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Вживаємо частку «не», а не «ні».", "Use particle 'не', not 'ні'."),
        ],
        "citation": "Правопис 2019, § 44, п. 1.3",
        "rule_ua": "Дієприкметник із часткою «не» пишеться окремо, якщо при ньому є пояснювальні (залежні) слова: ще не прочитаний лист; поле, не засіяне вчасно.",
        "rule_en": "A participle is written separately from 'не' when it has dependent/modifying words.",
    },
    {
        "id": "part_enclitic_bo_no_7",
        "category": FunctionWordCategory.PARTICLE_HYPHENATED_ENCLITICS,
        "cefr": "A2",
        "before": "Будь ласка,",
        "after": "уважніше цей абзац ще раз.",
        "correct": "прочитай-но",
        "distractors": [
            ("прочитайно", FunctionWordInterferenceType.MISSING_HYPHEN_PARTICLE, "Частки «-бо», «-но», «-то», «-от», «-таки» після слів, які вони підсилюють, пишуться через дефіс: «прочитай-но».", "Particles -бо, -но, -то, -от, -таки are attached with a hyphen when following the word they emphasize."),
            ("прочитай но", FunctionWordInterferenceType.MISSING_HYPHEN_PARTICLE, "Спонукальна частка «-но» після дієслова пишеться через дефіс, а не окремо.", "Cohortative particle '-но' is written with a hyphen after verbs."),
            ("прочитай-же", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Частка «же / ж» пишеться окремо від попереднього слова, без дефіса.", "Particle 'же / ж' is written separately without a hyphen."),
        ],
        "citation": "Правопис 2019, § 44, п. 3.1",
        "rule_ua": "Частки «-бо», «-но», «-то», «-от», «-таки» пишуться через дефіс, коли приєднуються безпосередньо до слова, яке вони виділяють: скажи-бо, прочитай-но, як-от, дійшов-таки.",
        "rule_en": "Particles -бо, -но, -то, -от, -таки are hyphenated when directly following the word they intensify.",
    },
    {
        "id": "part_taky_inverted_8",
        "category": FunctionWordCategory.PARTICLE_HYPHENATED_ENCLITICS,
        "cefr": "B1",
        "before": "Незважаючи на сильну втому, альпініст",
        "after": "дістався вершини гори.",
        "correct": "таки",
        "distractors": [
            ("таки-", FunctionWordInterferenceType.FALSE_HYPHEN_INVERTED_TAKY, "Частка «таки» пишеться через дефіс лише тоді, коли стоїть ПІСЛЯ дієслова («дістався-таки»). Якщо вона стоїть перед словом — пишеться окремо: «таки дістався».", "'Таки' is hyphenated only when standing AFTER the verb ('дістався-таки'). When standing BEFORE, it is written separately."),
            ("-таки", FunctionWordInterferenceType.FALSE_HYPHEN_INVERTED_TAKY, "Перед словом частка «таки» пишеться окремо без дефіса.", "Before the word, 'таки' is written separately without a hyphen."),
            ("такі", FunctionWordInterferenceType.FALSE_SOLID_PARTICLE, "«Таки» є незмінюваною часткою, а не закінченням прикметника у множині.", "The particle 'таки' is invariable."),
        ],
        "citation": "Правопис 2019, § 44, п. 3.1, прим. 2",
        "rule_ua": "Частка «таки» пишеться через дефіс лише після слова (дійшов-таки). Якщо вона стоїть перед словом — пишеться окремо: таки дійшов, таки знав.",
        "rule_en": "Particle 'таки' is hyphenated only when placed after the word (дійшов-таки); when placed before, it is written separately (таки дійшов).",
    },
    {
        "id": "part_prefix_split_9",
        "category": FunctionWordCategory.PARTICLE_PREFIX_SPLIT,
        "cefr": "B1",
        "before": "Він був людиною відкритою й міг зупинитися",
        "after": "на ніч під час подорожі.",
        "correct": "будь у кого",
        "distractors": [
            ("будь-у-кого", FunctionWordInterferenceType.FALSE_HYPHEN_PREPOSITIONAL_SPLIT, "Якщо між часткою («будь-», «хтозна-») та займенником стоїть прийменник, усі три слова пишуться окремо: «будь у кого».", "If a preposition stands between a particle and a pronoun, all three words are written separately: 'будь у кого'."),
            ("будь-у кого", FunctionWordInterferenceType.FALSE_HYPHEN_PREPOSITIONAL_SPLIT, "Дефіс не вживається, якщо вклинюється прийменник; пишуться три окремі слова.", "No hyphen is used when a preposition intervenes; written as three separate words."),
            ("будьукого", FunctionWordInterferenceType.FALSE_SOLID_PARTICLE, "Таке написання є грубою орфографічною помилкою; три слова пишуться окремо.", "Gross error; all three words must be written separately."),
        ],
        "citation": "Правопис 2019, § 44, п. 1; § 34",
        "rule_ua": "Частки «будь-», «казна-», «хтозна-» пишуться через дефіс (будь-хто, хтозна-де). Але якщо між часткою і займенником стоїть прийменник, усі слова пишуться окремо: будь у кого, хтозна з ким, казна за що.",
        "rule_en": "Particles будь-, казна-, хтозна- are hyphenated, but when a preposition intervenes, all three words are written separately: будь у кого.",
    },
    {
        "id": "part_ne_adj_solid_10",
        "category": FunctionWordCategory.PARTICLE_NE_SOLID,
        "cefr": "A2",
        "before": "Перед нами відкрився",
        "after": ", але дуже мальовничий краєвид.",
        "correct": "невеликий",
        "distractors": [
            ("не великий", FunctionWordInterferenceType.FALSE_SEPARATE_NE_NOUN_ADJ, "Прикметник «невеликий» пишеться разом, оскільки утворює нове поняття (= малий). Сполучник «але» не заперечує ознаки, а лише приєднує іншу рису.", "Adjective 'невеликий' is written solid when forming a new concept (= small). The conjunction 'але' does not negate the attribute."),
            ("не-великий", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Частка «не» з прикметниками через дефіс не пишеться.", "The particle 'не' is never hyphenated with adjectives."),
            ("нівеликий", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Префікс заперечення прикметників — «не-», а не «ні-».", "Prefix is 'не-', not 'ні-'."),
        ],
        "citation": "Правопис 2019, § 44, п. 2.7",
        "rule_ua": "«Не» з прикметниками пишеться разом, якщо утворює нове поняття (можна замінити синонімом без «не»: невеликий — малий). Сполучник «але» не вимагає окремого написання, на відміну від «а».",
        "rule_en": "'Не' is written solid with adjectives when forming a new concept replaceable by a synonym.",
    },
    {
        "id": "part_ne_adv_contrast_11",
        "category": FunctionWordCategory.PARTICLE_NE_CONTRAST_SEPARATE,
        "cefr": "A2",
        "before": "Наш новий офіс розташований",
        "after": ", а зовсім близько від метро.",
        "correct": "не далеко",
        "distractors": [
            ("недалеко", FunctionWordInterferenceType.FALSE_SOLID_NE_CONTRAST, "За наявності прямого протиставлення («не далеко, а близько») частка «не» з прислівником пишеться окремо.", "When directly contrasted with 'а', 'не' is written separately from the adverb."),
            ("не-далеко", FunctionWordInterferenceType.FALSE_HYPHEN_PARTICLE, "Частка «не» з прислівниками через дефіс не пишеться.", "The particle 'не' is never hyphenated with adverbs."),
            ("ні далеко", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Перед прислівником для заперечення ознаки вживаємо «не», а не «ні».", "Use particle 'не', not 'ні'."),
        ],
        "citation": "Правопис 2019, § 44, п. 1.4",
        "rule_ua": "Частка «не» пишеться окремо при протиставленні зі сполучником «а»: не далеко, а близько.",
        "rule_en": "Particle 'не' is written separately when directly contrasted with 'а': не далеко, а близько.",
    },
    {
        "id": "part_prefix_hyphen_12",
        "category": FunctionWordCategory.PARTICLE_HYPHENATED_ENCLITICS,
        "cefr": "A2",
        "before": "Це просте правило може пояснити",
        "after": "із присутніх учнів.",
        "correct": "будь-хто",
        "distractors": [
            ("будь хто", FunctionWordInterferenceType.MISSING_HYPHEN_PARTICLE, "Частки «будь-», «казна-», «хтозна-» з займенниками без прийменника пишуться через дефіс: «будь-хто».", "Particles будь-, казна-, хтозна- are hyphenated with pronouns when no preposition intervenes."),
            ("будьхто", FunctionWordInterferenceType.FALSE_SOLID_PARTICLE, "«Будь-хто» пишеться через дефіс, а не разом.", "Written with a hyphen, not solid."),
            ("хто будь", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "Нормативний порядок морфем — префіксальна частка попереду: «будь-хто».", "Standard order places 'будь-' before the pronoun."),
        ],
        "citation": "Правопис 2019, § 44, п. 3.2",
        "rule_ua": "Частки «будь-», «казна-», «хтозна-» пишуться через дефіс: будь-хто, будь-який, хтозна-хто.",
        "rule_en": "Particles будь-, казна-, хтозна- are written with a hyphen: будь-хто, хтозна-хто.",
    },
    {
        "id": "part_prefix_khtozna_13",
        "category": FunctionWordCategory.PARTICLE_HYPHENATED_ENCLITICS,
        "cefr": "B1",
        "before": "Він несподівано поїхав",
        "after": "й не залишив нової адреси.",
        "correct": "хтозна-куди",
        "distractors": [
            ("хтозна куди", FunctionWordInterferenceType.MISSING_HYPHEN_PARTICLE, "Частка «хтозна-» з прислівниками пишеться через дефіс: «хтозна-куди».", "Particle 'хтозна-' with adverbs is written with a hyphen."),
            ("хтознакуди", FunctionWordInterferenceType.FALSE_SOLID_PARTICLE, "«Хтозна-куди» пишеться через дефіс, а не одним словом.", "Written with a hyphen, not as a single word."),
            ("хтозна-де", FunctionWordInterferenceType.LEXICAL_SEMANTIC_CONFUSION, "«Хтозна-де» вказує на місцеперебування («де?»), тоді як дієслово «поїхав» вимагає позначення напрямку («куди? — хтозна-куди»).", "'Хтозна-де' indicates static location ('where?'), whereas movement requires direction ('хтозна-куди')."),
        ],
        "citation": "Правопис 2019, § 44, п. 3.2",
        "rule_ua": "Частка «хтозна-» з прислівниками пишеться через дефіс: хтозна-куди, хтозна-як, хтозна-де.",
        "rule_en": "Particle 'хтозна-' with adverbs is written with a hyphen: хтозна-куди, хтозна-де.",
    },
]


# ============================================================================
# Rule Resolution Engine (Правопис 2019, §§ 42–44)
# ============================================================================


def resolve_preposition_hyphenation(prep: str) -> tuple[bool, str, str]:
    """Determine if a compound preposition requires a hyphen per Правопис 2019 (§ 42, п. 1 та 2)."""
    norm = prep.strip().lower()
    if norm.startswith(("з-", "із-")):
        return (
            True,
            "Складні прийменники з першою частиною «з-», «із-» пишуться через дефіс (з-під, з-за, із-за, з-поміж, з-понад) (Правопис 2019, § 42, п. 2).",
            "Compound prepositions with initial z-/iz- are hyphenated (з-під, з-за, із-за, з-поміж, з-понад).",
        )
    return (
        False,
        "Складні прийменники без «з-», «із-» пишуться разом (посеред, задля, внаслідок) (Правопис 2019, § 42, п. 1).",
        "Compound prepositions without initial z-/iz- are written solid (посеред, задля, внаслідок).",
    )


def resolve_causal_preposition(is_positive_factor: bool) -> tuple[str, str, str]:
    """Determine correct causal preposition (завдяки vs через) based on semantic polarity."""
    if is_positive_factor:
        return (
            "завдяки",
            "«Завдяки» вживаємо лише з давальним відмінком для вираження позитивних, сприятливих чинників.",
            "Use 'завдяки' (+ Dative) exclusively for positive or favorable factors.",
        )
    return (
        "через",
        "«Через» вживаємо зі знахідним відмінком для небажаних, шкідливих або нейтральних причин.",
        "Use 'через' (+ Accusative) for adverse, undesirable, or neutral causes.",
    )


def resolve_duration_preposition(is_time_duration: bool) -> tuple[str, str, str]:
    """Determine duration preposition: 'протягом'/'упродовж' vs 'на протязі'."""
    if is_time_duration:
        return (
            "протягом",
            "На позначення тривалості в часі вживаємо «протягом» або «упродовж».",
            "Use 'протягом' or 'упродовж' to express duration in time.",
        )
    return (
        "на протязі",
        "Вислів «на протязі» вживається лише в прямому значенні струменя повітря між відчиненими вікнами чи дверима.",
        "The phrase 'на протязі' refers strictly to being in an air draft between open doors or windows.",
    )


def resolve_conjunction_homophone(pair: str, is_conjunction: bool) -> tuple[str, str, str]:
    """Distinguish conjunction from homophonous pronoun/particle sequences per Правопис 2019 (§ 43, п. 1 та примітка)."""
    p = pair.strip().lower()
    if p in ("prote", "проте"):
        if is_conjunction:
            return (
                "проте",
                "Сполучник «проте» (= але, однак) пишеться разом (Правопис 2019, § 43, п. 1 та примітка).",
                "Conjunction 'проте' (= but, however) is written solid.",
            )
        return (
            "про те",
            "Прийменник із вказівним займенником «про те» пишеться окремо (про що? — про те).",
            "Preposition with demonstrative pronoun 'про те' is written separately (about what? -> about that).",
        )
    elif p in ("zate", "зате"):
        if is_conjunction:
            return (
                "зате",
                "Сполучник «зате» (= але) пишеться разом (Правопис 2019, § 43, п. 1 та примітка).",
                "Conjunction 'зате' (= but) is written solid.",
            )
        return (
            "за те",
            "Прийменник із займенником «за те» пишеться окремо (за що? — за те).",
            "Preposition with pronoun 'за те' is written separately.",
        )
    elif p in ("shchob", "щоб"):
        if is_conjunction:
            return (
                "щоб",
                "Сполучник мети та з'ясувальний «щоб» пишеться разом (Правопис 2019, § 43, п. 1 та примітка).",
                "Purpose and explanatory conjunction 'щоб' is written solid.",
            )
        return (
            "що б",
            "Займенник «що» з часткою «б» пишеться окремо (частку можна переставити).",
            "Interrogative/relative pronoun 'що' with particle 'б' is written separately.",
        )
    elif p in ("yakby", "якби"):
        if is_conjunction:
            return (
                "якби",
                "Умовний сполучник «якби» (= якщо б) пишеться разом (Правопис 2019, § 43, п. 1 та примітка).",
                "Conditional conjunction 'якби' (= if) is written solid.",
            )
        return (
            "як би",
            "Прислівник способу дії «як» із часткою «би» пишеться окремо.",
            "Adverb of manner 'як' with modal particle 'би' is written separately.",
        )
    elif p in ("yakshcho", "якщо"):
        if is_conjunction:
            return (
                "якщо",
                "Умовний сполучник «якщо» пишеться разом (Правопис 2019, § 43, п. 1 та примітка).",
                "Conditional conjunction 'якщо' (= if) is written solid.",
            )
        return (
            "як що",
            "Прислівник «як» із займенником «що» пишуться окремо, коли кожне слово має самостійне значення й відповідає на окреме питання.",
            "Adverb 'як' and pronoun 'що' are written separately when each preserves independent syntactic function.",
        )
    elif p in ("takozh", "також"):
        if is_conjunction:
            return (
                "також",
                "Приєднувальний сполучник «також» пишеться разом (Правопис 2019, § 43, п. 1; Академічна граматика; СУМ-20).",
                "Joining conjunction 'також' is written solid.",
            )
        return (
            "так же",
            "Прислівник «так» із підсилювальною часткою «же» пишеться окремо (Правопис 2019, § 44, п. 1.13; СУМ-20).",
            "Adverb 'так' with particle 'же' is written separately.",
        )
    elif p in ("tezh", "теж"):
        if is_conjunction:
            return (
                "теж",
                "Приєднувальний сполучник «теж» пишеться разом (Правопис 2019, § 43, п. 1; Академічна граматика; СУМ-20).",
                "Joining conjunction 'теж' is written solid.",
            )
        return (
            "те ж",
            "Вказівний займенник «те» з часткою «ж» пишеться окремо (Правопис 2019, § 44, п. 1.13; СУМ-20).",
            "Demonstrative pronoun 'те' with particle 'ж' is written separately.",
        )
    raise ValueError(f"Unknown conjunction homophone pair: {pair}")


def resolve_particle_ne(
    pos: str,
    has_contrast: bool = False,
    has_dependent_words: bool = False,
    cannot_stand_without_ne: bool = False,
    forms_new_concept: bool = True,
) -> tuple[str, str, str]:
    """Orthography of 'не' per Правопис 2019 (§ 44, п. 1 та 2). Returns ('разом' | 'окремо', rule_ua, rule_en)."""
    pos_norm = pos.strip().lower()

    if cannot_stand_without_ne:
        return (
            "разом",
            "Слова, які без «не» не вживаються, завжди пишуться разом: ненавидіти, нехтувати, неволити, негайний (Правопис 2019, § 44, п. 2.5).",
            "Words that cannot stand without 'не' are always written solid: ненавидіти, нехтувати.",
        )

    if has_contrast:
        return (
            "окремо",
            "Частка «не» пишеться окремо, якщо є протиставлення зі сполучником «а», що заперечує ознаку: не глибокий, а мілкий; не далеко, а близько (Правопис 2019, § 44, п. 1.4).",
            "Particle 'не' is written separately when there is explicit contrast with 'а' negating the property: не глибокий, а мілкий.",
        )

    if pos_norm in ("verb", "дієслово", "gerund", "дієприслівник"):
        return (
            "окремо",
            "Частка «не» з дієсловами та дієприслівниками пишеться окремо: не знаю, не пишучи (Правопис 2019, § 44, п. 1.1 та 1.2).",
            "Particle 'не' is written separately with verbs and gerunds: не знаю, не пишучи.",
        )

    if pos_norm in ("participle", "дієприкметник"):
        if has_dependent_words:
            return (
                "окремо",
                "Частка «не» з дієприкметниками пишеться окремо, якщо при них є пояснювальні (залежні) слова: ще не прочитана книга (Правопис 2019, § 44, п. 1.3).",
                "Particle 'не' is written separately with participles having dependent modifying words: ще не прочитана книга.",
            )
        return (
            "разом",
            "Одиничний дієприкметник без залежних слів, що виступає означенням, пишеться з «не» разом: непрочитана книга (Правопис 2019, § 44, п. 2.8).",
            "An isolated participle without dependent words acting as an attribute is written solid: непрочитана книга.",
        )

    if pos_norm in ("noun", "іменник", "adj", "adjective", "прикметник", "adv", "adverb", "прислівник"):
        if forms_new_concept:
            return (
                "разом",
                "З іменниками, прикметниками та прислівниками «не» пишеться разом, коли утворює нове поняття (можна замінити синонімом: неправда — брехня) (Правопис 2019, § 44, п. 2.7).",
                "With nouns, adjectives, and adverbs, 'не' is written solid when forming a new concept (replaceable with a synonym).",
            )
        return (
            "окремо",
            "Якщо слово з «не» не утворює нового поняття і лише заперечує ознаку, воно пишеться окремо (Правопис 2019, § 44, п. 1.4).",
            "If 'не' merely negates without forming a unified lexical concept, it is written separately.",
        )

    return (
        "окремо",
        "За загальним правилом частка «не» пишеться окремо (Правопис 2019, § 44, п. 1).",
        "As a general rule, particle 'не' is written separately.",
    )


def resolve_particle_hyphenation(
    particle: str,
    position_after_word: bool = True,
    has_intervening_preposition: bool = False,
) -> tuple[str, str, str]:
    """Orthography of particles per Правопис 2019 (§ 44, п. 1 та 3). Returns ('дефіс' | 'окремо', rule_ua, rule_en)."""
    p_norm = particle.strip().lower().replace("-", "")

    if p_norm in ("будь", "казна", "хтозна"):
        if has_intervening_preposition:
            return (
                "окремо",
                "Якщо між частками «будь-», «казна-», «хтозна-» та займенником стоїть прийменник, усі три слова пишуться окремо: будь у кого, хтозна з ким (Правопис 2019, § 44, п. 1; § 34).",
                "When a preposition intervenes between будь-, казна-, хтозна- and a pronoun, all three words are written separately: будь у кого.",
            )
        return (
            "дефіс",
            "Частки «будь-», «казна-», «хтозна-» з іншими словами пишуться через дефіс: будь-хто, хтозна-де (Правопис 2019, § 44, п. 3.2).",
            "Particles будь-, казна-, хтозна- are hyphenated: будь-хто, хтозна-де.",
        )

    if p_norm == "таки":
        if position_after_word:
            return (
                "дефіс",
                "Частка «таки» пишеться через дефіс, коли стоїть ПІСЛЯ слова, яке виділяє: прийшов-таки, знав-таки (Правопис 2019, § 44, п. 3.1).",
                "Particle 'таки' is hyphenated when standing AFTER the word it emphasizes: прийшов-таки.",
            )
        return (
            "окремо",
            "Частка «таки» пишеться окремо, коли стоїть ПЕРЕД словом: таки прийшов, таки переміг (Правопис 2019, § 44, п. 3.1, прим. 2).",
            "Particle 'таки' is written separately when standing BEFORE the word: таки прийшов.",
        )

    if p_norm in ("бо", "но", "то", "от"):
        return (
            "дефіс",
            f"Частки «-{p_norm}» після слів, які вони виділяють, пишуться через дефіс (Правопис 2019, § 44, п. 3.1).",
            f"Particles '-{p_norm}' are hyphenated when following the emphasized word.",
        )

    return (
        "окремо",
        "Частка пишеться окремо (Правопис 2019, § 44, п. 1).",
        "Particle is written separately.",
    )


def build_canonical_function_word_cards() -> list[FunctionWordCard]:
    """Compile the authoritative set of canonical Function Word practice cards."""
    all_raw_items = (
        CANONICAL_PREPOSITION_HYPHENATED_ITEMS
        + CANONICAL_PREPOSITION_COMPOUND_SOLID_ITEMS
        + CANONICAL_PREPOSITION_LOCUTIONS_ITEMS
        + CANONICAL_PREPOSITION_GOVERNMENT_ITEMS
        + CANONICAL_CONJUNCTION_ITEMS
        + CANONICAL_PARTICLE_ITEMS
    )

    cards: list[FunctionWordCard] = []
    for item in all_raw_items:
        distractors = [
            FunctionWordDistractor(
                form=unicodedata.normalize("NFC", d[0]).strip(),
                interference_type=d[1],
                explanation_ua=unicodedata.normalize("NFC", d[2]).strip(),
                explanation_en=unicodedata.normalize("NFC", d[3]).strip(),
            )
            for d in item["distractors"]
        ]
        card = FunctionWordCard(
            card_id=unicodedata.normalize("NFC", item["id"]).strip(),
            category=item["category"],
            cefr_level=unicodedata.normalize("NFC", item["cefr"]).strip().upper(),
            sentence_before=unicodedata.normalize("NFC", item["before"]).strip(),
            sentence_after=unicodedata.normalize("NFC", item["after"]).strip(),
            correct_answer=unicodedata.normalize("NFC", item["correct"]).strip(),
            distractors=distractors,
            rule_citation=unicodedata.normalize("NFC", item["citation"]).strip(),
            rule_summary_ua=unicodedata.normalize("NFC", item["rule_ua"]).strip(),
            rule_summary_en=unicodedata.normalize("NFC", item["rule_en"]).strip(),
        )
        cards.append(card)

    return cards


def validate_function_word_card(card: FunctionWordCard) -> list[str]:
    """Hermetic verification of a function word card ensuring zero collisions, valid CEFR, and full metadata."""
    errors: list[str] = []

    if not card.card_id:
        errors.append("card_id is empty")
    if not card.correct_answer:
        errors.append("correct_answer is empty")

    valid_cefr = {"A1", "A2", "B1", "B2", "C1", "C2"}
    if card.cefr_level not in valid_cefr:
        errors.append(f"invalid cefr_level '{card.cefr_level}', expected one of {valid_cefr}")

    # Options count and zero-collision check (normalized)
    if len(card.distractors) != 3:
        errors.append(f"expected exactly 3 distractors, got {len(card.distractors)}")

    normalized_correct = unicodedata.normalize("NFC", card.correct_answer).strip().casefold()
    seen_normalized_forms = {normalized_correct}

    for idx, d in enumerate(card.distractors):
        if not d.form:
            errors.append(f"distractor[{idx}] form is empty")
        norm_d = unicodedata.normalize("NFC", d.form).strip().casefold()
        if norm_d in seen_normalized_forms:
            errors.append(f"collision detected: distractor '{d.form}' duplicates existing option '{norm_d}'")
        seen_normalized_forms.add(norm_d)

        if not d.explanation_ua:
            errors.append(f"distractor[{idx}] explanation_ua is empty")
        if not d.explanation_en:
            errors.append(f"distractor[{idx}] explanation_en is empty")
        if not isinstance(d.interference_type, FunctionWordInterferenceType):
            errors.append(f"distractor[{idx}] invalid interference_type: {d.interference_type}")

    if not card.rule_citation:
        errors.append("rule_citation is empty")
    if not card.rule_summary_ua:
        errors.append("rule_summary_ua is empty")
    if not card.rule_summary_en:
        errors.append("rule_summary_en is empty")

    return errors


def export_function_word_deck(cards: list[FunctionWordCard], output_path: Path | None = None) -> dict[str, Any]:
    """Export function word cards to standard JSON structure for practice consumption."""
    deck = {
        "version": "1.0",
        "title": "Ukrainian Function Words Practice (Службові частини мови)",
        "categories": [c.value for c in FunctionWordCategory],
        "total_cards": len(cards),
        "cards": [
            {
                "id": c.card_id,
                "category": c.category.value,
                "cefrLevel": c.cefr_level,
                "prompt": c.prompt_display,
                "fullSentence": c.full_sentence,
                "sentenceBefore": c.sentence_before,
                "sentenceAfter": c.sentence_after,
                "correctAnswer": c.correct_answer,
                "options": c.all_options(),
                "distractors": [
                    {
                        "form": d.form,
                        "interferenceType": d.interference_type.value,
                        "explanationUa": d.explanation_ua,
                        "explanationEn": d.explanation_en,
                    }
                    for d in c.distractors
                ],
                "ruleCitation": c.rule_citation,
                "ruleSummary": {
                    "uk": c.rule_summary_ua,
                    "en": c.rule_summary_en,
                },
            }
            for c in cards
        ],
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return deck


def main() -> int:
    """CLI runner to validate and export canonical function word practice deck."""
    parser = argparse.ArgumentParser(description="Ukrainian Function Words Practice Engine.")
    parser.add_argument("--output", type=Path, help="Target JSON output path for practice deck.")
    parser.add_argument("--validate-only", action="store_true", help="Run validation without writing file.")
    args = parser.parse_args()

    cards = build_canonical_function_word_cards()
    total_errors = 0

    for card in cards:
        errs = validate_function_word_card(card)
        if errs:
            print(f"Error in card {card.card_id}: {errs}", file=sys.stderr)
            total_errors += len(errs)

    if total_errors > 0:
        print(f"Validation failed with {total_errors} errors.", file=sys.stderr)
        return 1

    print(f"✅ Successfully validated {len(cards)} Function Word practice cards with 0 collisions.")

    default_output = PROJECT_ROOT / "registry" / "practice" / "function_words_deck.json"
    target_output = args.output or (default_output if not args.validate_only else None)

    if target_output:
        export_function_word_deck(cards, target_output)
        print(f"Exported deck to {target_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
