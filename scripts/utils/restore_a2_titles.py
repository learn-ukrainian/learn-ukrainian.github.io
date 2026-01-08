import os
import yaml
import re

def restore_a2_titles():
    a2_dir = "curriculum/l2-uk-en/a2"
    meta_dir = os.path.join(a2_dir, "meta")
    fixed_count = 0
    
    for filename in os.listdir(a2_dir):
        if filename.endswith(".md"):
            path = os.path.join(a2_dir, filename)
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines: continue
            
            first_line = lines[0].strip()
            if first_line in ["# Summary", "# Підсумок"]:
                # Try to find meta
                slug = filename.replace(".md", "")
                meta_path = os.path.join(meta_dir, slug + ".yaml")
                
                title = "Ukrainian Lesson"
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as mf:
                        meta = yaml.safe_load(mf)
                        title = meta.get('title', title)
                        subtitle = meta.get('subtitle', "")
                        if subtitle:
                            title = f"{title} | {subtitle}"
                
                lines[0] = f"# {title}\n"
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                fixed_count += 1
                print(f"Restored title in {filename}: {title}")

    print(f"Finished. Restored {fixed_count} titles.")

if __name__ == "__main__":
    restore_a2_titles()
