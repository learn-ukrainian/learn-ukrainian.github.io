import yaml
import sys

# LIT-MAIN is already correct (186 modules) in the manifest, 
# so we only need to define the EXPANDED specialized tracks here.

NEW_TRACKS = {
    "lit-essay": {
        "type": "track",
        "modules": [
            "essay-origins-polemics", "kostomarov-two-rus-nationalities",
            "drahomanov-chudatski-dumky", "drahomanov-shevchenko",
            "franko-what-is-progress", "franko-some-words",
            "lesia-ukrainka-voice", "mikhnovsky-independent-ukraine",
            "lypynsky-letters-brothers", "lypynsky-ham-japheth",
            "dontsov-nationalism", "dontsov-chaos",
            "khvylovy-ukraine-or-little-russia", "khvylovy-thoughts-current",
            "zerov-ad-fontes", "malaniuk-little-russianism",
            "sherekh-fifth-kharkiv", "shevelov-moscow-maros", "shevelov-history-language",
            "dziuba-internationalism", "stus-phenomenon",
            "sverstiuk-cathedral", "lysiah-rudnytsky-history",
            "grabowicz-poet-prophet", "zabuzhko-fortinbras",
            "zabuzhko-notre-dame", "zabuzhko-longest-journey",
            "riabchuk-two-ukraines", "hrytsak-history-ukraine", "hrytsak-overcoming-past",
            "prokhasko-fm-halychyna", "portnikov-bells", "portnikov-conclusion",
            "yermolenko-fluid-ideologies", "snyder-dialogues",
            "mariia-berlinska-dignity", "chmut-institutions", "kotsyubailo-legacy",
            "essay-capstone-1", "essay-capstone-2"
        ]
    },
    "lit-kids": {
        "type": "track",
        "modules": [
            "franko-fox-mykyta", "pchilka-fables", "zavadovych-adventures",
            "nestayko-toreadors-1", "nestayko-toreadors-2", "nestayko-toreadors-3",
            "nestayko-forest-school", "nestayko-fantasy",
            "blyznets-zemlyanyk", "malyk-alice",
            "rutkivsky-dzhury", "rutkivsky-dzhury-2",
            "malkovych-poems", "dermansky-monsters", "dermansky-chu-drove",
            "vynnychuk-lviv-tales", "starovyt-my-kyiv",
            "oksenyk-forest-valley", "bachynsky-140-decibels", "pavliuk-rytm",
            "andrusyak-rabbits", "lutsyshyna-whale",
            "kids-poetry-anthology", "kids-folklore", "kids-capstone"
        ]
    },
    "lit-fantastika": {
        "type": "track",
        "modules": [
            "gogol-viy-ukrainian", "kvitka-dead-mans-easter", "storozhenko-devil",
            "kotsiubynsky-shadows-revisit", "vynnychenko-solar-machine-revisit",
            "smolych-beautiful-catastrophes",
            "berdnyk-star-corsair-1", "berdnyk-star-corsair-2", "berdnyk-prometheus",
            "rosokhovatsky-cyborgs",
            "vynnychuk-tango-death", "vynnychuk-night-maiden",
            "pavliuk-flesh", "dyachenko-ritual", "dyachenko-vita-nostra",
            "arenev-powder", "arenev-soul-traps",
            "korniy-chimaeras", "korniy-forest", "dashvar-village",
            "kidruk-bots", "kidruk-colony", "babenko-witch",
            "fantastika-anthology", "fantastika-capstone"
        ]
    },
    "lit-hist-fic": {
        "type": "track",
        "modules": [
            "kulish-black-council-revisit", "starytsky-bohdan", "lepkyi-mazepa",
            "zahrebelny-roksolana-1", "zahrebelny-roksolana-2", "zahrebelny-dyvo", "zahrebelny-death-in-kyiv",
            "ivanychuk-malvy", "ivanychuk-water", "ivanychuk-scar",
            "bilyk-sword-ares",
            "shklyar-black-raven-1", "shklyar-black-raven-2", "shklyar-marusia",
            "lys-century-jacob", "kokotyukha-red", "kokotyukha-chervonyi",
            "kourkov-grey-bees", "rafeyenko-long-times", "hist-fic-capstone"
        ]
    }
}

PATH = "curriculum/l2-uk-en/curriculum.yaml"

def main():
    try:
        with open(PATH, 'r') as f:
            data = yaml.safe_load(f)
        
        # Add/Update the specialized tracks
        for track_name, track_data in NEW_TRACKS.items():
            print(f"Updating/Adding track: {track_name} ({len(track_data['modules'])} modules)")
            data['levels'][track_name] = track_data

        # Remove 'lit-sci' and 'lit-teen' if they exist (renamed/merged)
        if 'lit-sci' in data['levels']:
            del data['levels']['lit-sci']
            print("Removed deprecated track: lit-sci")
        if 'lit-teen' in data['levels']:
            del data['levels']['lit-teen']
            print("Removed deprecated track: lit-teen")

        # Write Back
        with open(PATH, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print("Success!")

    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()
