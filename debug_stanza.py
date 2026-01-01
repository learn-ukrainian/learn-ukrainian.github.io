
import stanza
import sys

def debug_stanza_lemma(text_input):
    nlp = stanza.Pipeline('uk', processors='tokenize,mwt,pos,lemma', verbose=False)
    
    print(f"\n--- Isolated Test: '{text_input}' ---")
    doc = nlp(text_input)
    for sent in doc.sentences:
        for word in sent.words:
            print(f"Word: {word.text} -> Lemma: {word.lemma} (POS: {word.pos})")

    print(f"\n--- Context Test: 'Це є {text_input}.' ---")
    doc2 = nlp(f"Це є {text_input}.")
    for sent in doc2.sentences:
        for word in sent.words:
            # We want the word that matches our input (or part of it)
            if word.text.lower() in text_input.lower() or text_input.lower() in word.text.lower():
                 print(f"Context Word: {word.text} -> Lemma: {word.lemma} (POS: {word.pos})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_stanza_lemma(sys.argv[1])
    else:
        debug_stanza_lemma("пілота")
