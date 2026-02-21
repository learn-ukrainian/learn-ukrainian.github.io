import json
import yaml
import os
import re
from pathlib import Path

def load_podcasts():
    with open('docs/resources/podcasts/podcast_db.json', 'r') as f:
        return json.load(f)

def get_modules(level):
    modules = []
    level_path = Path(f'curriculum/l2-uk-en/{level.lower()}')
    if not level_path.exists():
        return []
    
    for f in sorted(level_path.glob('*.md')):
        slug = f.stem
        title = ""
        with open(f, 'r') as m:
            for line in m:
                if line.startswith('title:'):
                    title = line.replace('title:', '').strip().strip('"')
                    break
        if not title:
            title = slug.replace('-', ' ').title()
        
        modules.append({
            'id': f"{level.lower()}-{slug}",
            'slug': slug,
            'title': title,
            'level': level.upper()
        })
    return modules

def get_ep_level(ep):
    if 'level' in ep:
        return ep['level']
    
    tags = ep.get('tags', [])
    if 'Season 1' in tags: return 'A1'
    if 'Season 2' in tags: return 'A2'
    if 'Season 3' in tags: return 'B1'
    if 'Season 4' in tags: return 'B2'
    if 'Season 5' in tags: return 'C1'
    if 'Season 6' in tags: return 'C2'
    
    if 'FMU' in ep['id']: return 'A1'
    return None

def map_episodes(podcasts, modules):
    # Expanded grammar and topic mapping
    topic_map = {
        'accusative': ['accusative', 'кого', 'що', 'знахідний'],
        'genitive': ['genitive', 'кого', 'чого', 'немає', 'родовий'],
        'dative': ['dative', 'кому', 'чому', 'давальний'],
        'instrumental': ['instrumental', 'ким', 'чим', 'орудний'],
        'locative': ['locative', 'де', 'на чому', 'місцевий'],
        'aspect': ['aspect', 'доконаний', 'недоконаний', 'perfective', 'imperfective'],
        'motion': ['motion', 'йти', 'їхати', 'ходити', 'їздити', 'пересуватися'],
        'reflexive': ['reflexive', 'ся', 'зворотні'],
        'comparison': ['comparison', 'comparative', 'superlative', 'кращий', 'ступені'],
        'history': ['history', 'історія', 'past', 'минуле'],
        'food': ['food', 'їжа', 'restaurant', 'cafe', 'кухня', 'страв'],
        'family': ['family', 'сім\'я', 'родина'],
        'weather': ['weather', 'погода', 'nature', 'природа'],
        'body': ['body', 'тіло', 'health', 'здоров\'я', 'лікар'],
        'shopping': ['shopping', 'магазин', 'купувати', 'ціна'],
        'time': ['time', 'час', 'година', 'котра'],
        'clothes': ['clothes', 'одяг', 'вдягатися'],
        'education': ['education', 'навчання', 'школа', 'університет'],
        'work': ['work', 'робота', 'професія'],
        'travel': ['travel', 'подорож', 'туризм'],
        'music': ['music', 'музика', 'пісня'],
        'cinema': ['cinema', 'кіно', 'фільм'],
        'technology': ['technology', 'технології', 'інтернет'],
        'politics': ['politics', 'політика', 'суспільство'],
    }

    # Stop words that cause bad matches
    stop_words = {'my', 'world', 'living', 'code', 'checkpoint', 'first', 'second', 'part', 'the', 'and', 'for'}

    mappings = []
    for module in modules:
        recommended = []
        
        module_title_lower = module['title'].lower()
        
        # Determine module's core keywords
        module_keywords = set(re.sub(r'[^\w\s]', ' ', module_title_lower).split())
        module_keywords = {kw for kw in module_keywords if kw not in stop_words and len(kw) > 2}
        
        # Add related keywords from topic_map
        for key, synonyms in topic_map.items():
            if key in module_title_lower:
                module_keywords.update(synonyms)

        for ep in podcasts:
            ep_title = ep['title'].lower()
            ep_summary = ep.get('summary', '').lower()
            ep_level = get_ep_level(ep)
            
            match_reason = ""
            relevance = "low"
            
            # Level relations
            level_match = (ep_level == module['level'])
            is_progressive_review = (ep_level == 'A1' and module['level'] in ['A2', 'B1', 'B2'])
            is_challenge = (ep_level in ['B1', 'B2'] and module['level'] == 'A2')
            
            title_hits = [kw for kw in module_keywords if kw in ep_title and len(kw) > 3]
            summary_hits = [kw for kw in module_keywords if kw in ep_summary and len(kw) > 3]

            if title_hits:
                if level_match:
                    match_reason = f"Level-aligned topic match: {', '.join(title_hits[:3])}"
                    relevance = "high"
                elif is_progressive_review:
                    match_reason = f"Listening review (A1): {', '.join(title_hits[:3])}"
                    relevance = "medium"
                elif is_challenge:
                    match_reason = f"Challenge listening ({ep_level}): {', '.join(title_hits[:3])}"
                    relevance = "medium"
                else:
                    match_reason = f"Cross-level topic match: {', '.join(title_hits[:3])}"
                    relevance = "medium"
            
            elif summary_hits:
                if level_match:
                    match_reason = f"Summary match: {', '.join(summary_hits[:3])}"
                    relevance = "medium"
                elif is_progressive_review:
                    match_reason = f"Review listening in summary: {', '.join(summary_hits[:3])}"
                    relevance = "low"

            if match_reason:
                recommended.append({
                    'episode_id': ep['id'],
                    'title': ep['title'],
                    'url': ep['url'],
                    'match_reason': match_reason,
                    'relevance': relevance
                })
        
        if recommended:
            # Sort by relevance, then favor ULP over FMU, then title hits over summary hits
            recommended.sort(key=lambda x: (
                x['relevance'] != 'high', 
                x['relevance'] != 'medium',
                'FMU' in x['episode_id'],
                'match' not in x['match_reason'].lower()
            ))
            
            mappings.append({
                'module_id': module['id'],
                'module_title': module['title'],
                'level': module['level'],
                'recommended_episodes': recommended[:5]
            })
            
    return mappings

def main():
    podcasts = load_podcasts()
    all_mappings = []
    
    levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    for level in levels:
        modules = get_modules(level)
        mappings = map_episodes(podcasts, modules)
        all_mappings.extend(mappings)
        print(f"Mapped {len(mappings)}/{len(modules)} modules for {level}")

    output = {
        'generated_at': '2026-01-02',
        'mappings': all_mappings
    }
    
    os.makedirs('docs/resources/podcasts', exist_ok=True)
    
    with open('docs/resources/podcasts/ulp_mapping.yaml', 'w') as f:
        yaml.dump(output, f, sort_keys=False, allow_unicode=True)

if __name__ == "__main__":
    main()