import os
import sys

sys.path.append(os.getcwd() + "/scripts")
try:
    from audit.checks.richness_config import CULTURAL_TERMS, UKRAINIAN_PLACES
    print("PLACES:", list(UKRAINIAN_PLACES)[:10])
    print("TERMS:", list(CULTURAL_TERMS)[:10])
except Exception as e:
    print(e)
