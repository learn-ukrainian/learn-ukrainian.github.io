import os
import yaml
import re

# Standard Aliases
ALIASES = {
    "Summary": "Summary|Підсумок",
    "Підсумок": "Summary|Підсумок",
    "Warm-up": "Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка",
    "Вступ": "Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка",
    "Контекст": "Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка",
    "Presentation": "Presentation|Grammar|Focus|Презентація|Граматика|Теорія",
    "Презентація": "Presentation|Grammar|Focus|Презентація|Граматика|Теорія",
    "Grammar": "Presentation|Grammar|Focus|Презентація|Граматика|Теорія",
    "Practice": "Practice|Exercises|Activity|Практика|Вправи",
    "Практика": "Practice|Exercises|Activity|Практика|Вправи"
}

def standardize_templates():
    template_dir = "docs/l2-uk-en/templates"
    updated_count = 0
    
    for filename in os.listdir(template_dir):
        if filename.endswith(".md"):
            path = os.path.join(template_dir, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the TEMPLATE_METADATA block
            match = re.search(r'TEMPLATE_METADATA:\s*\n(.*?)\n-->', content, re.DOTALL)
            if match:
                meta_str = match.group(1)
                try:
                    meta = yaml.safe_load(meta_str)
                    if 'required_sections' in meta:
                        new_sections = []
                        changed = False
                        for section in meta['required_sections']:
                            # If it's already a flexible string (contains |), keep it or expand it
                            base_section = section.split('|')[0].strip()
                            if base_section in ALIASES:
                                if section != ALIASES[base_section]:
                                    new_sections.append(ALIASES[base_section])
                                    changed = True
                                else:
                                    new_sections.append(section)
                            else:
                                new_sections.append(section)
                        
                        if changed:
                            meta['required_sections'] = new_sections
                            # Convert back to YAML
                            new_meta_str = yaml.dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
                            indented_meta = "\n".join(["  " + line for line in new_meta_str.strip().split("\n")])
                            new_content = content[:match.start(1)] + indented_meta + content[match.end(1):]
                            
                            with open(path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            updated_count += 1
                            print(f"Standardized {filename}")
                except Exception as e:
                    print(f"Error in {filename}: {e}")
    
    print(f"Finished. Standardized {updated_count} templates.")

if __name__ == "__main__":
    standardize_templates()
