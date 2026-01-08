import os
import yaml
import re

def update_templates():
    template_dir = "docs/l2-uk-en/templates"
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
                    # Parse as YAML
                    meta = yaml.safe_load(meta_str)
                    if 'required_sections' in meta:
                        if "Need More Practice?" not in meta['required_sections']:
                            meta['required_sections'].append("Need More Practice?")
                            
                            # Convert back to YAML with proper indentation
                            new_meta_str = yaml.dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
                            # Indent for the HTML comment
                            indented_meta = "\n".join(["  " + line for line in new_meta_str.strip().split("\n")])
                            
                            new_content = content[:match.start(1)] + indented_meta + content[match.end(1):]
                            
                            with open(path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"Updated {filename}")
                        else:
                            print(f"Skipping {filename} (already present)")
                except Exception as e:
                    print(f"Error parsing metadata in {filename}: {e}")

if __name__ == "__main__":
    update_templates()
