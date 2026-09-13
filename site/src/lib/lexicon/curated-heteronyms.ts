import type { EntryRecord } from "./atlas-data-source";
import type { LexiconEntry } from "./atlasDb";

export const CURATED_HETERONYMS: Record<string, LexiconEntry[]> = {
  город: [
    {
      headword: "горо́д",
      short_label: "ділянка землі (A2)",
      gloss: "vegetable garden, garden plot",
      pos: "noun",
      cefr: "A2",
      heritage_status: {
        classification: "standard",
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
      },
      pronunciation: {
        ipa: "[ɦɔˈrɔd]",
        source: "VESUM",
      },
      stress: {
        form: "горо́д",
        source: "ukrainian-word-stress",
      },
      morphology: {
        pos: "іменник",
        paradigm: {
          kind: "noun",
          cases: {
            називний: { singular: "горо́д", plural: "горо́ди" },
            родовий: { singular: "горо́ду", plural: "городі́в" },
            давальний: { singular: "горо́дові / горо́ду", plural: "горо́дам" },
            знахідний: { singular: "горо́д", plural: "горо́ди" },
            орудний: { singular: "горо́дом", plural: "горо́дами" },
            місцевий: { singular: "на горо́ді / горо́ду", plural: "горо́дах" },
            кличний: { singular: "горо́де", plural: "горо́ди" },
          },
        },
        stress: {
          source: "ukrainian-word-stress",
          forms: {
            городу: "горо́ду",
            городом: "горо́дом",
            городі: "горо́ді",
            городе: "горо́де",
            городи: "горо́ди",
            городів: "городі́в",
            городам: "горо́дам",
            городами: "горо́дами",
            городах: "горо́дах",
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-20",
          items: ["грядка", "городчик"],
        },
        idioms: {
          items: [
            {
              phrase: "город (рідше тин) городити",
              definition: "Починати якусь копітку справу.",
              source: "Фразеологічний словник української мови",
            },
            {
              phrase: "камінь у чийсь город",
              definition: "Недоброзичливий натяк кому-небудь.",
              source: "Фразеологічний словник української мови",
            },
          ],
          source: "Фразеологічний словник української мови",
        },
        proverbs: {
          items: [
            {
              text: "В хаті гульки, а в городі ані цибульки",
              gloss: "Глум з господині, що гуляє, а не пильнує господарства.",
              source: "Приповідки або українсько-народня філософія",
            },
            {
              text: "Мій город, як моя комора",
              gloss: "Огородина в літі помагає багато в харчі.",
              source: "Приповідки або українсько-народня філософія",
            },
            {
              text: "Не лазь у городи, бо наробиш шкоди",
              gloss: "До чужого діла не мішайся, бо не знаєш його.",
              source: "Приповідки або українсько-народня філософія",
            },
          ],
          source: "Приповідки або українсько-народня філософія",
        },
      },
      examples: [
        {
          uk: "На вихідни́х ми бу́демо працюва́ти на горо́ді.",
          en: "On the weekend, we will work in the vegetable garden.",
          source: "Anna Ohoiko",
          locator: "ohoiko-1000-words entry 168",
        },
      ],
      distinction_note:
        "Не плутати з омографом «го́род» (наголос на першому складі: застаріле «місто», фортеця).",
    },
    {
      headword: "го́род",
      short_label: "заст. місто",
      gloss: "city, town, fortified settlement (archaic)",
      pos: "noun",
      heritage_status: {
        classification: "authentic-archaism",
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
        warning_severity: "treasured",
        attestations: [
          {
            source: "esum",
            ref: "город:1:570",
            word: "город",
            detail: "город (заст. розм.) «місто», город (< огород) «квітник біля хати»",
          },
        ],
      },
      pronunciation: {
        ipa: "[ˈɦɔrɔd]",
        source: "kaikki/Wiktionary (CC BY-SA 3.0)",
      },
      stress: {
        form: "го́род",
        source: "kaikki/Wiktionary (CC BY-SA 3.0)",
      },
      morphology: {
        pos: "іменник",
        paradigm: {
          kind: "noun",
          cases: {
            називний: { singular: "го́род", plural: "городи́" },
            родовий: { singular: "го́рода (го́роду)", plural: "городі́в" },
            давальний: { singular: "го́родові / го́роду", plural: "города́м" },
            знахідний: { singular: "го́род", plural: "городи́" },
            орудний: { singular: "го́родом", plural: "города́ми" },
            місцевий: { singular: "у го́роді", plural: "города́х" },
            кличний: { singular: "го́роде", plural: "городи́" },
          },
        },
        stress: {
          source: "Правописний словник Голоскевича (1929)",
          forms: {
            города: "го́рода",
            городу: "го́роду",
            городом: "го́родом",
            городі: "го́роді",
            городи: "городи́",
            городів: "городі́в",
            городам: "города́м",
            городами: "города́ми",
            городах: "города́х",
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-11: Те саме, що → місто",
          items: ["місто"],
        },
      },
      examples: [
        {
          uk: "В тім городі жила Дидона, А город звався Карфаген.",
          en: "In that city lived Dido, and the city was called Carthage.",
          source: "Іван Котляревський, «Енеїда»",
          locator: "Котл., І, 1952, 71",
        },
      ],
      distinction_note:
        "Не плутати з сучасним словом «горо́д» (наголос на другому складі: ділянка землі біля хати для вирощування овочів).",
    },
  ],
  замок: [
    {
      headword: "за́мок",
      short_label: "палац, фортеця",
      gloss: "castle, fortress, palace",
      pos: "noun",
      cefr: "A2",
      heritage_status: {
        classification: "standard",
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
      },
      pronunciation: {
        ipa: "[ˈzamɔk]",
        source: "kaikki/Wiktionary",
      },
      stress: {
        form: "за́мок",
        source: "ukrainian-word-stress",
      },
      morphology: {
        pos: "іменник",
        paradigm: {
          kind: "noun",
          cases: {
            називний: { singular: "за́мок", plural: "замки́" },
            родовий: { singular: "за́мку", plural: "замкі́в" },
            давальний: { singular: "за́мку / за́мкові", plural: "замка́м" },
            знахідний: { singular: "за́мок", plural: "замки́" },
            орудний: { singular: "за́мком", plural: "замка́ми" },
            місцевий: { singular: "у за́мку", plural: "замка́х" },
            кличний: { singular: "за́мку", plural: "замки́" },
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-20 / Караванський",
          items: ["фортеця", "твердиня", "палац", "цитадель"],
        },
      },
      examples: [
        {
          uk: "Старовинний за́мок височів над долиною.",
          en: "The ancient castle towered over the valley.",
          source: "СУМ-11",
        },
      ],
      distinction_note:
        "Не плутати з омографом «замо́к» (наголос на другому складі: пристрій для замикання дверей).",
    },
    {
      headword: "замо́к",
      short_label: "пристрій для замикання",
      gloss: "lock (door lock, padlock)",
      pos: "noun",
      cefr: "A2",
      heritage_status: {
        classification: "standard",
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
      },
      pronunciation: {
        ipa: "[zɐˈmɔk]",
        source: "kaikki/Wiktionary",
      },
      stress: {
        form: "замо́к",
        source: "ukrainian-word-stress",
      },
      morphology: {
        pos: "іменник",
        paradigm: {
          kind: "noun",
          cases: {
            називний: { singular: "замо́к", plural: "замки́" },
            родовий: { singular: "замка́", plural: "замкі́в" },
            давальний: { singular: "замку́ / замко́ві", plural: "замка́м" },
            знахідний: { singular: "замо́к", plural: "замки́" },
            орудний: { singular: "замко́м", plural: "замка́ми" },
            місцевий: { singular: "у замку́", plural: "замка́х" },
            кличний: { singular: "замку́", plural: "замки́" },
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-20",
          items: ["колодка", "засув", "клямка"],
        },
      },
      examples: [
        {
          uk: "Він замкнув двері на замо́к.",
          en: "He locked the door with a lock.",
          source: "СУМ-11",
        },
      ],
      distinction_note:
        "Не плутати з омографом «за́мок» (наголос на першому складі: фортеця або середньовічний палац).",
    },
  ],
  атлас: [
    {
      headword: "а́тлас",
      short_label: "збірник карт",
      gloss: "atlas (bound collection of maps)",
      pos: "noun",
      cefr: "A2",
      heritage_status: {
        classification: "standard",
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
      },
      pronunciation: {
        ipa: "[ˈatɫɐs]",
        source: "VESUM",
      },
      stress: {
        form: "а́тлас",
        source: "ukrainian-word-stress",
      },
      morphology: {
        pos: "іменник",
        paradigm: {
          kind: "noun",
          cases: {
            називний: { singular: "а́тлас", plural: "а́тласи" },
            родовий: { singular: "а́тласу", plural: "а́тласів" },
            давальний: { singular: "а́тласу / а́тласові", plural: "а́тласам" },
            знахідний: { singular: "а́тлас", plural: "а́тласи" },
            орудний: { singular: "а́тласом", plural: "а́тласами" },
            місцевий: { singular: "в а́тласі", plural: "а́тласах" },
            кличний: { singular: "а́тласе", plural: "а́тласи" },
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-11",
          items: ["збірник карт", "альбом карт", "географічний атлас"],
        },
      },
      distinction_note:
        "Не плутати з омографом «атла́с» (наголос на другому складі: шовкова тканина).",
    },
    {
      headword: "атла́с",
      short_label: "тканина",
      gloss: "satin (glossy silk fabric)",
      pos: "noun",
      cefr: "B1",
      heritage_status: {
        classification: "standard",
        is_russianism: false,
        russian_shadow: false,
        vesum_attested: true,
      },
      pronunciation: {
        ipa: "[ɐtˈɫas]",
        source: "VESUM",
      },
      stress: {
        form: "атла́с",
        source: "ukrainian-word-stress",
      },
      morphology: {
        pos: "іменник",
        paradigm: {
          kind: "noun",
          cases: {
            називний: { singular: "атла́с", plural: "атла́си" },
            родовий: { singular: "атла́су", plural: "атла́сів" },
            давальний: { singular: "атла́су / атла́сові", plural: "атла́сам" },
            знахідний: { singular: "атла́с", plural: "атла́си" },
            орудний: { singular: "атла́сом", plural: "атла́сами" },
            місцевий: { singular: "в атла́сі", plural: "атла́сах" },
            кличний: { singular: "атла́се", plural: "атла́си" },
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-11",
          items: ["шовк", "сатин", "шовкова тканина"],
        },
      },
      distinction_note:
        "Не плутати з омографом «а́тлас» (наголос на першому складі: збірник географічних або анатомічних карт).",
    },
  ],
};

export function getEffectiveHeteronyms(
  record: EntryRecord | null | undefined,
): LexiconEntry[] | null {
  if (record?.entry?.heteronyms && record.entry.heteronyms.length > 1) {
    return record.entry.heteronyms;
  }
  const slug = (record?.slug || record?.entry?.lemma || "").toLowerCase().trim();
  if (slug && CURATED_HETERONYMS[slug]) {
    return CURATED_HETERONYMS[slug];
  }
  return null;
}
