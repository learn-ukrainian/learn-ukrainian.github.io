
import sys
import hashlib
from pathlib import Path

def compute_hash(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Simulate what audit_module likely does. 
    # If it uses audit.core.get_content_hash(file_path), let's try to import it.
    try:
        from audit.core import get_content_hash
        return get_content_hash(file_path)
    except ImportError:
        # Fallback to standard md5 of utf-8 bytes
        return hashlib.md5(content.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_hash.py <file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    print(f"Hash for {file_path}: {compute_hash(file_path)}")
