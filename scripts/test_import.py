import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
try:
    from yaml_activities import ActivityParser
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
