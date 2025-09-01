import re

def pick_index(question: str)->str:
    q = question.lower()
    # heurística: perguntas “sobre o projeto” vão p/ interno, o resto p/ literatura
    if re.search(r"\b(ke(c|g)|ag5|zuco|nosso|nossa|pipeline|protocolo|seed|figura|apêndice|método usado)\b", q):
        return "internal"
    return "lit2025"
