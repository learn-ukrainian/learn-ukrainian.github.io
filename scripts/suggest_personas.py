#!/usr/bin/env python3
"""
Persona Suggestion & Injection Script v3.1 (Senior Optimized)

1. Scans ALL tracks for modules missing personas.
2. Processes in giant batches of 250 using gemini-3-pro-preview.
3. Injects deterministic personas into plan YAMLs.
"""

import sys
import yaml
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any

# Centralized config source
from scripts.config import TRACK_CONFIG

def extract_yaml(text: str) -> Dict:
    """Extracts suggestions from LLM output, handling various formats."""
    # 1. Clean up backticks and markdown markers
    text = text.replace("```yaml", "").replace("```", "")
    
    # 2. Look for the last block starting with suggestions:
    matches = re.findall(r"(suggestions:.*?)(\n\n|───|\Z)", text, re.DOTALL)
    if matches:
        try:
            return yaml.safe_load(matches[-1][0])
        except yaml.YAMLError as e:
            print(f"YAML Parse Error in match: {e}")
    
    # 3. Fallback to simple line-based extraction
    lines = text.splitlines()
    yaml_lines = []
    found = False
    for line in lines:
        if line.strip().startswith("suggestions:"): found = True
        if found:
            # Stop if we hit a bridge delimiter
            if line.startswith("───") or line.startswith("==="): break
            yaml_lines.append(line)
    
    if yaml_lines:
        try:
            return yaml.safe_load("\n".join(yaml_lines))
        except yaml.YAMLError as e:
            print(f"YAML Parse Error in fallback: {e}")
            
    return {}

def get_batch_persona_suggestions(track: str, batch_data: List[Dict]) -> Dict:
    """Sends giant batch to Gemini and gets a mapping back."""
    # Get primary voice from TRACK_CONFIG
    track_info = TRACK_CONFIG.get(track, {})
    primary_voice = track_info.get("persona", "Senior Specialist")
    
    module_list_str = ""
    for item in batch_data:
        module_list_str += f"- slug: {item['slug']}\n  title: \"{item['title']}\"\n"

    prompt = f"""
ROLE: You are an Elite Curriculum Director. 
TASK: Suggest authentic 'Situational Roles' for this batch of Ukrainian modules.

PRIMARY VOICE: {primary_voice}

MODULES:
{module_list_str}

INSTRUCTIONS:
1. Provide a unique, culturally authentic 'role' for each slug.
2. Vary the roles (e.g. Architect, Village Elder, Logistics Expert, Diplomat, Chronicler).
3. RETURN ONLY VALID YAML.

OUTPUT FORMAT:
suggestions:
  slug-name: "Role Name"
"""
    
    try:
        cmd = [
            ".venv/bin/python", "scripts/ai_agent_bridge.py", "ask-gemini",
            prompt, "--task-id", f"scale-persona-{track}", "--stdout-only", "--model", "gemini-3-pro-preview"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return extract_yaml(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error calling Gemini: {e}")
    except Exception as e:
        print(f"Unexpected error in scale suggestion: {e}")
    return {}

def process_all_tracks(batch_size: int = 250):
    plan_root = Path("curriculum/l2-uk-en/plans")
    if not plan_root.exists():
        print(f"Error: Plan directory {plan_root} not found.")
        return

    tracks = [d.name for d in plan_root.iterdir() if d.is_dir()]
    
    for track in tracks:
        print(f"\n🌍 Processing track: {track}")
        plan_dir = plan_root / track
        
        queue = []
        for plan_file in plan_dir.glob("*.yaml"):
            try:
                with open(plan_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data: continue
                
                # Persona missing or too short
                if "persona" not in data or len(data.get("persona", {}).get("role", "")) < 5:
                    queue.append({"slug": plan_file.stem, "title": data.get("title", "Unknown"), "path": plan_file})
            except (yaml.YAMLError, OSError) as e:
                print(f"  ⚠️ Skipping {plan_file.name}: {e}")
                continue

        if not queue:
            print(f"  ✅ Track {track} is fully cast.")
            continue

        print(f"  📦 Found {len(queue)} modules. Grouping into batches of {batch_size}...")
        
        for i in range(0, len(queue), batch_size):
            chunk = queue[i:i + batch_size]
            print(f"  🚀 Requesting batch {i//batch_size + 1}...")
            
            suggestions = get_batch_persona_suggestions(track, chunk)
            
            if suggestions and "suggestions" in suggestions:
                mapping = suggestions["suggestions"]
                track_info = TRACK_CONFIG.get(track, {})
                primary_voice = track_info.get("persona", "Senior Specialist")
                
                for item in chunk:
                    role = mapping.get(item["slug"])
                    if role:
                        try:
                            with open(item["path"], "r", encoding="utf-8") as f: 
                                data = yaml.safe_load(f)
                            data["persona"] = {"voice": primary_voice, "role": role}
                            with open(item["path"], "w", encoding="utf-8") as f: 
                                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
                        except (yaml.YAMLError, OSError) as e:
                            print(f"  ⚠️ Error writing to {item['slug']}: {e}")
                print(f"  ✨ Batch {i//batch_size + 1} complete.")
            else:
                print(f"  ❌ Batch {i//batch_size + 1} failed.")

if __name__ == "__main__":
    try:
        size = int(sys.argv[1]) if len(sys.argv) > 1 else 250
        process_all_tracks(size)
    except KeyboardInterrupt:
        print("\n👋 Processed interrupted by user.")
        sys.exit(0)
