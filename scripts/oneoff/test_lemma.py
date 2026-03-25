import sys
sys.path.append('.')
from scripts.rag.vesum_client import get_lemma_forms
print(get_lemma_forms("айтівець"))
print(get_lemma_forms("айтівка"))
