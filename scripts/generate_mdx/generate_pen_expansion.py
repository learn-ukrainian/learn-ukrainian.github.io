from pathlib import Path

import yaml

data = {
    "lit-doc": [
        {
            "slug": "yermolenko-philosophical-narrative",
            "title": "Volodymyr Yermolenko: The Philosophical Narrative",
            "focus": "Philosophical essay as a genre, Fluid Ideologies.",
            "research": "## The Intellectual Landscape\nYermolenko bridges philosophy, literature, and European history. His essays (e.g., 'Fluid Ideologies') deconstruct Russian imperialism through a distinctly Ukrainian philosophical lens.\n\n## Decolonization Focus\nAnalyze his use of the essay format to restore Ukrainian subjectivity in the European intellectual space."
        },
        {
            "slug": "matviichuk-human-rights",
            "title": "Oleksandra Matviichuk: Human Rights as Literature",
            "focus": "The language of justice, documentary testimony.",
            "research": "## The Literature of Fact\nMatviichuk's Nobel Peace Prize lecture and human rights documentation represent a new genre of 'legal literature' in Ukraine, turning raw data of war crimes into compelling global narratives.\n\n## Decolonization Focus\nThe shift from victimhood to active legal and moral agency."
        },
        {
            "slug": "kipiani-case-of-stus",
            "title": "Vakhtang Kipiani: The Case of Vasyl Stus",
            "focus": "Archival documentation, historical justice.",
            "research": "## Archival Restoration\nKipiani's compilation of KGB archives regarding poet Vasyl Stus transforms bureaucratic terror records into a literary monument of resistance.\n\n## Decolonization Focus\nExposing the mechanics of Soviet censorship and the complicity of individuals (e.g., Medvedchuk) in the intellectual genocide of the Shistdesiatnyky."
        },
        {
            "slug": "amelina-women-looking-at-war",
            "title": "Victoria Amelina: Women Looking at War",
            "focus": "Posthumous legacy, war documentation, Truth Hounds.",
            "research": "## The Witness\nAmelina transitioned from a celebrated novelist to a war crimes investigator. Her essays and poetry document the destruction of Ukrainian cultural heritage (e.g., Kapitolivka).\n\n## Decolonization Focus\nThe role of the female intellectual in preserving national memory during existential conflict."
        }
    ],
    "lit-drama": [
        {
            "slug": "vorozhbyt-bad-roads",
            "title": "Natalia Vorozhbyt: Bad Roads",
            "focus": "Post-Maidan theater, trauma, documentary drama.",
            "research": "## The New Drama\nVorozhbyt captures the fractured, raw, and often brutal reality of the Donbas conflict. Her plays utilize authentic vernacular and Surzhyk to reflect wartime trauma.\n\n## Decolonization Focus\nRejecting idealized or sanitized depictions of war in favor of raw, localized psychological realism."
        },
        {
            "slug": "arie-chornobyl",
            "title": "Pavlo Arie: At the Beginning and End of Time",
            "focus": "Chornobyl zone, Chthonic mythology, modern stage.",
            "research": "## Chthonic Realism\nArie's work explores the Exclusion Zone not just as a historical disaster, but as a mythical, liminal space inhabited by marginalized figures (Baba Prisia).\n\n## Decolonization Focus\nReclaiming the Chornobyl narrative from Soviet bureaucratic failure and Western sci-fi, grounding it in Ukrainian folk trauma."
        },
        {
            "slug": "tsilyk-cinematic-script",
            "title": "Iryna Tsilyk: From Poetry to the Cinematic Script",
            "focus": "Cross-medium storytelling, documentary filmmaking.",
            "research": "## The Visual Narrative\nTsilyk's transition from poetry to directing (e.g., 'The Earth Is Blue as an Orange') represents the integration of lyrical text into visual documentary.\n\n## Decolonization Focus\nEmpowering civilian and youth voices in the war zone through the lens of art and cinema."
        }
    ],
    "lit-crimea": [
        {
            "slug": "dzhelyal-letters-from-cell",
            "title": "Nariman Dzhelyal: Letters from the Cell",
            "focus": "Prison prose, intellectual resistance, Qırımtatar identity.",
            "research": "## The Voice of the Peninsula\nDzhelyal's writings smuggled out of Russian prisons serve as a powerful continuation of the dissident 'prison literature' tradition, adapted for the Crimean Tatar struggle.\n\n## Decolonization Focus\nThe intersection of Ukrainian and Qırımtatar political resistance against modern Russian occupation."
        },
        {
            "slug": "aliev-musayeva-dzhemilev",
            "title": "Alim Aliev & Sevgil Musayeva: Mustafa Dzhemilev",
            "focus": "Biographical narrative, the Crimean Tatar national movement.",
            "research": "## The Living Legend\nThis biographical work documents the life of Mustafa Dzhemilev, framing the historical struggle of the Crimean Tatars (the Surgunlik) through the lens of continuous, non-violent resistance.\n\n## Decolonization Focus\nCentering the indigenous narrative of Crimea and rejecting the imperial 'Russian Crimea' myth."
        },
        {
            "slug": "krymskyi-historical-poetry",
            "title": "Ahatanhel Krymskyi: Historical Crimean Poetry",
            "focus": "Orientalism, early 20th-century literature.",
            "research": "## The Scholar-Poet\nKrymskyi, a polyglot and foundational figure of the Ukrainian Academy of Sciences, wrote extensively on Eastern cultures and Crimea. His poetry blends Ukrainian modernism with oriental motifs.\n\n## Decolonization Focus\nEstablishing Ukraine's direct, non-imperial intellectual connection to the Islamic world and the East, bypassing St. Petersburg."
        }
    ]
}

curriculum_dir = Path("curriculum/l2-uk-en")
plans_dir = curriculum_dir / "plans"

for track, modules in data.items():
    for index, mod in enumerate(modules, start=10):
        slug = mod["slug"]

        plan_content = {
            "slug": slug,
            "level": "c1",
            "sequence": index,
            "track": track,
            "word_target": 5000,
            "focus": mod["focus"]
        }

        plan_path = plans_dir / track / f"{slug}.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(plan_content, f, sort_keys=False, allow_unicode=True)

        research_content = f"# Research Notes: {mod['title']}\n\n**Track**: {track} | **Module**: {slug} | **Researched**: 2026-02-24\n\n{mod['research']}\n\n## Seminar-Specific Analysis\n> [!analysis] Deep Dive: This module integrates contemporary PEN Ukraine voices, ensuring a decolonized, academically rigorous exploration of modern Ukrainian intellectual life.\n\n## Primary Sources\n- PEN Ukraine Member Profiles.\n- Native Ukrainian essays and documentary publications.\n"

        research_dir = curriculum_dir / track / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        research_path = research_dir / f"{slug}-research.md"
        with open(research_path, "w", encoding="utf-8") as f:
            f.write(research_content)

print("Generated PEN Ukraine Expansion Plans and Research Notes.")
