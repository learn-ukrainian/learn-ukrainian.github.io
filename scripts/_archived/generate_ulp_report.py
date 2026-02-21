import yaml
import json

def generate_report():
    with open('docs/resources/podcasts/ulp_mapping.yaml', 'r') as f:
        mapping = yaml.safe_load(f)
    
    with open('docs/resources/podcasts/podcast_db.json', 'r') as f:
        podcasts = json.load(f)
    
    total_episodes = len(podcasts)
    mappings = mapping['mappings']
    
    level_stats = {}
    episodes_used = set()
    
    for m in mappings:
        lvl = m['level']
        if lvl not in level_stats:
            level_stats[lvl] = 0
        level_stats[lvl] += 1
        
        for ep in m['recommended_episodes']:
            episodes_used.add(ep['episode_id'])
            
    # Module counts (manual for now based on file listing)
    module_counts = {
        'A1': 34,
        'A2': 57,
        'B1': 91,
        'B2': 131,
        'C1': 0, # Currently empty
        'C2': 0
    }
    
    report = "# ULP Mapping Report\n\n"
    report += f"**Date:** 2026-01-02\n"
    report += f"**Episodes analyzed:** {total_episodes}\n"
    report += f"**Modules mapped:** {len(mappings)}\n\n"
    
    report += "## Coverage Summary\n\n"
    report += "| Level | Modules | Mapped | Coverage |\n"
    report += "|-------|---------|--------|----------|\n"
    
    total_modules = 0
    total_mapped = 0
    
    for lvl in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        count = module_counts.get(lvl, 0)
        mapped = level_stats.get(lvl, 0)
        total_modules += count
        total_mapped += mapped
        coverage = (mapped / count * 100) if count > 0 else 0
        report += f"| {lvl} | {count} | {mapped} | {coverage:.1f}% |\n"
        
    total_coverage = (total_mapped / total_modules * 100) if total_modules > 0 else 0
    report += f"| **Total** | **{total_modules}** | **{total_mapped}** | **{total_coverage:.1f}%** |\n\n"
    
    report += "## Episode Usage\n\n"
    report += f"- Total episodes in ULP database: {total_episodes}\n"
    report += f"- Episodes used in mappings: {len(episodes_used)}\n"
    report += f"- Percentage of library utilized: {(len(episodes_used)/total_episodes*100):.1f}%\n"
    report += f"- Average episodes per mapped module: {(sum(len(m['recommended_episodes']) for m in mappings)/len(mappings)):.1f}\n\n"
    
    report += "## High-Confidence Mappings (Examples)\n\n"
    for m in mappings[:10]:
        best_ep = m['recommended_episodes'][0]
        if best_ep['relevance'] == 'high':
            report += f"- **{m['module_id']}**: {best_ep['title']} ({best_ep['match_reason']})\n"
            
    report += "\n## Recommendations\n\n"
    report += "- **B2 History Gap**: ULP has limited content on specific historical periods (Trypillian, Scythians). Alternative resources (YouTube/Articles) are needed for M71-M131.\n"
    report += "- **C1/C2 Content**: No modules currently exist for C1/C2. Once created, Season 5/6 episodes should be mapped.\n"
    report += "- **FMU Integration**: FMU episodes are excellent for A1/A2 quick reviews and should be prioritized for mobile-friendly practice.\n"

    with open('docs/resources/podcasts/ULP_MAPPING_REPORT.md', 'w') as f:
        f.write(report)
    print("Report generated: docs/resources/podcasts/ULP_MAPPING_REPORT.md")

if __name__ == "__main__":
    generate_report()
