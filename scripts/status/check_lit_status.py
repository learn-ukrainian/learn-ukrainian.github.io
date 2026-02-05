import os
import yaml
from pathlib import Path

def check_lit_status():
    lit_dir = Path("curriculum/l2-uk-en/lit")
    modules = sorted([f.stem for f in lit_dir.glob("*.md") if f.stem != "README"])
    
    report = []
    
    for mod in modules:
        mod_status = {"id": mod}
        
        # Check MD content
        md_path = lit_dir / f"{mod}.md"
        if md_path.exists():
            content = md_path.read_text()
            mod_status["md_size"] = len(content)
            mod_status["has_frontmatter"] = content.startswith("---")
            mod_status["has_vocab_table"] = "# Словник" in content or "## Словник" in content or "| Слово |" in content
            mod_status["has_resources_block"] = "[!resources]" in content
        
        # Check YAMLs
        for yaml_type in ["meta", "vocabulary", "activities"]:
            yaml_path = lit_dir / yaml_type / f"{mod}.yaml"
            mod_status[f"has_{yaml_type}"] = yaml_path.exists()
            if yaml_type == "vocabulary" and yaml_path.exists():
                try:
                    with open(yaml_path, 'r') as f:
                        v_data = yaml.safe_load(f)
                        items = v_data.get("items", [])
                        if items:
                            first_item = items[0]
                            mod_status["vocab_schema"] = "new" if "lemma" in first_item else "old"
                            mod_status["has_ipa"] = "ipa" in first_item
                        else:
                            mod_status["vocab_schema"] = "empty"
                except:
                    mod_status["vocab_schema"] = "error"

        report.append(mod_status)
    
    # Print report
    print(f"{'Module':<35} | MD Size | FM | Vocab | Res | Meta | Voc | Act | Sch | IPA")
    print("-" * 110)
    for r in report:
        print(f"{r['id']:<35} | {r.get('md_size', 0):>7} | {str(r.get('has_frontmatter'))[0]} | {str(r.get('has_vocab_table'))[0]} | {str(r.get('has_resources_block'))[0]} | {str(r.get('has_meta'))[0]} | {str(r.get('has_vocabulary'))[0]} | {str(r.get('has_activities'))[0]} | {r.get('vocab_schema', 'N/A'):<4} | {str(r.get('has_ipa', 'F'))[0]}")

if __name__ == "__main__":
    check_lit_status()
