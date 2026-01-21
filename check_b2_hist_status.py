import yaml
import os

def check_status():
    manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    b2_hist_modules = manifest['levels']['b2-hist']['modules']
    base_dir = "curriculum/l2-uk-en/b2-hist"
    
    stats = {
        'total': len(b2_hist_modules),
        'md_exists': 0,
        'meta_exists': 0,
        'vocab_exists': 0,
        'activities_exists': 0,
        'fully_migrated': 0
    }
    
    missing_md = []
    missing_meta = []
    missing_vocab = []
    missing_activities = []
    
    for slug in b2_hist_modules:
        md_path = os.path.join(base_dir, f"{slug}.md")
        meta_path = os.path.join(base_dir, "meta", f"{slug}.yaml")
        vocab_path = os.path.join(base_dir, "vocabulary", f"{slug}.yaml")
        activities_path = os.path.join(base_dir, "activities", f"{slug}.yaml")
        
        md_ok = os.path.exists(md_path)
        meta_ok = os.path.exists(meta_path)
        vocab_ok = os.path.exists(vocab_path)
        activities_ok = os.path.exists(activities_path)
        
        if md_ok: stats['md_exists'] += 1
        else: missing_md.append(slug)
        
        if meta_ok: stats['meta_exists'] += 1
        else: missing_meta.append(slug)
        
        if vocab_ok: stats['vocab_exists'] += 1
        else: missing_vocab.append(slug)
        
        if activities_ok: stats['activities_exists'] += 1
        else: missing_activities.append(slug)
        
        if md_ok and meta_ok and vocab_ok and activities_ok:
            stats['fully_migrated'] += 1
            
    print(f"B2-HIST Status Report")
    print(f"=====================")
    print(f"Total Modules in Manifest: {stats['total']}")
    print(f"Markdown Files (.md):      {stats['md_exists']} / {stats['total']}")
    print(f"Metadata (meta/):           {stats['meta_exists']} / {stats['total']}")
    print(f"Vocabulary (vocabulary/):   {stats['vocab_exists']} / {stats['total']}")
    print(f"Activities (activities/):   {stats['activities_exists']} / {stats['total']}")
    print(f"Fully Migrated (All 4):    {stats['fully_migrated']} / {stats['total']}")
    
    if missing_md:
        print(f"\nMissing MD files ({len(missing_md)}):")
        print(", ".join(missing_md[:10]) + ("..." if len(missing_md) > 10 else ""))
        
    if missing_meta:
        print(f"\nMissing Metadata ({len(missing_meta)}):")
        print(", ".join(missing_meta[:10]) + ("..." if len(missing_meta) > 10 else ""))

    if missing_vocab:
        print(f"\nMissing Vocabulary ({len(missing_vocab)}):")
        print(", ".join(missing_vocab[:10]) + ("..." if len(missing_vocab) > 10 else ""))

    if missing_activities:
        print(f"\nMissing Activities ({len(missing_activities)}):")
        print(", ".join(missing_activities[:10]) + ("..." if len(missing_activities) > 10 else ""))

if __name__ == "__main__":
    check_status()
