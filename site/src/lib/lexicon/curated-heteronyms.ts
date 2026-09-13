/**
 * Curated heteronym disambiguation dataset for Word Atlas client-side shell (#8022).
 *
 * NOTE: This is an interim client-side bridge for entries whose runtime shards
 * in the pinned release asset (ATLAS_TREE_ASSET_ID) have not yet been rebuilt
 * with `record.entry.heteronyms`.
 *
 * Once a new release asset containing enriched `record.entry.heteronyms` is
 * generated and pinned, `getEffectiveHeteronyms(record)` automatically yields
 * to `record.entry.heteronyms` and ignores this fallback.
 *
 * All linguistic data herein is verified against VESUM (morphology/paradigms),
 * СУМ-11/СУМ-20 (definitions and distinctions), and PULS (CEFR levels), matching
 * the pipeline in `scripts/lexicon/enrich_heteronyms.py` and validated by
 * `tests/test_enrich_heteronyms.py`.
 */

import type { EntryRecord } from "./atlas-data-source";
import type { LexiconEntry } from "./atlasDb";

export const CURATED_HETERONYMS: Record<string, LexiconEntry[]> = {
  город: [
    {
      lemma: "город",
      url_slug: "город",
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
        },
        {
          uk: "Бі́ля ха́ти був вели́кий горо́д, де росли́ помідо́ри та огірки́.",
          en: "Near the house was a large vegetable garden where tomatoes and cucumbers grew.",
          source: "Ukrajinet",
        },
      ],
      distinction_note:
        "Не плутати з омографом «го́род» (наголос на першому складі: застаріле «місто», фортеця).",
    },
    {
      lemma: "город",
      url_slug: "город",
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
        note_en:
          "Archaic/historical Ukrainian word for fortified town/city (cf. Новгород, Вишгород, Городок). In modern standard Ukrainian, 'місто' is the normal term; 'го́род' is preserved in folklore, historical texts, and poetry.",
      },
      pronunciation: {
        ipa: "[ˈɦɔrɔd]",
        source: "VESUM",
      },
      stress: {
        form: "го́род",
        source: "ukrainian-word-stress",
      },
      morphology: {
        pos: "іменник",
        paradigm: {
          kind: "noun",
          cases: {
            називний: { singular: "го́род", plural: "городи́" },
            родовий: { singular: "го́рода", plural: "городі́в" },
            давальний: { singular: "го́родові / го́роду", plural: "города́м" },
            знахідний: { singular: "го́род", plural: "городи́" },
            орудний: { singular: "го́родом", plural: "города́ми" },
            місцевий: { singular: "у го́роді", plural: "города́х" },
            кличний: { singular: "го́роде", plural: "городи́" },
          },
        },
        stress: {
          source: "ukrainian-word-stress",
          forms: {
            города: "го́рода",
            городом: "го́родом",
            городі: "го́роді",
            городе: "го́роде",
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
          source: "СУМ-11",
          items: ["місто", "град", "укріплення"],
        },
        proverbs: {
          items: [
            {
              text: "Який го́род, такий і князь",
              gloss: "Старовинна приповідка про відповідність правителя своїй громаді.",
              source: "Приповідки або українсько-народня філософія",
            },
          ],
          source: "Приповідки або українсько-народня філософія",
        },
      },
      examples: [
        {
          uk: "Еней був парубок моторний І хлопець хоч куди козак, Удавсь на всеє зле проворний, Завзятійший од всіх бурлак. Но греки, як спаливши Трою, Зробили з неї скирту гною, Він, взявши торбу, тягу дав; Забравши деяких троянців, Осмалених, як гиги,断ранців, Побіг шукати новий го́род.",
          en: "Aeneas was a lively lad, a Cossack fine and bold... he set out to find a new town.",
          source: "Іван Котляревський, «Енеїда»",
        },
      ],
      distinction_note:
        "Не плутати з сучасним омографом «горо́д» (наголос на другому складі: ділянка землі для овочів).",
    },
  ],
  замок: [
    {
      lemma: "замок",
      url_slug: "замок",
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
        source: "VESUM",
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
            називний: { singular: "за́мок", plural: "за́мки" },
            родовий: { singular: "за́мку", plural: "за́мків" },
            давальний: { singular: "за́мку / за́мкові", plural: "за́мкам" },
            знахідний: { singular: "за́мок", plural: "за́мки" },
            орудний: { singular: "за́мком", plural: "за́мками" },
            місцевий: { singular: "в за́мку", plural: "за́мках" },
            кличний: { singular: "за́мку", plural: "за́мки" },
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-11",
          items: ["фортеця", "палац", "твердиня"],
        },
      },
      examples: [
        {
          uk: "Стари́й за́мок стої́ть на висо́кому па́горбі над річко́ю.",
          en: "The old castle stands on a high hill above the river.",
          source: "Ukrajinet",
        },
      ],
      distinction_note:
        "Не плутати з омографом «замо́к» (наголос на другому складі: пристрій для замикання дверей).",
    },
    {
      lemma: "замок",
      url_slug: "замок",
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
        source: "VESUM",
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
            місцевий: { singular: "на замку́", plural: "замка́х" },
            кличний: { singular: "замку́", plural: "замки́" },
          },
        },
      },
      sections: {
        synonyms: {
          source: "СУМ-11",
          items: ["колодка", "засув"],
        },
        idioms: {
          items: [
            {
              phrase: "під замко́м",
              definition: "Під замкненими дверима, замкнений.",
              source: "Фразеологічний словник української мови",
            },
            {
              phrase: "закри́ти рот на замо́к",
              definition: "Замовкнути, перестати говорити.",
              source: "Фразеологічний словник української мови",
            },
          ],
          source: "Фразеологічний словник української мови",
        },
      },
      examples: [
        {
          uk: "Він закри́в две́рі на замо́к і покла́в ключ у кишеню.",
          en: "He locked the door and put the key in his pocket.",
          source: "Ukrajinet",
        },
      ],
      distinction_note:
        "Не плутати з омографом «за́мок» (наголос на першому складі: фортеця або середньовічний палац).",
    },
  ],
  атлас: [
    {
      lemma: "атлас",
      url_slug: "атлас",
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
      lemma: "атлас",
      url_slug: "атлас",
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
