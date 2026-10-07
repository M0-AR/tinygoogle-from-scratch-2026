"""Part 5a — Query path: intersect, score, snippet."""
from .index import tokenize
from .rank import bm25, final_score


def search(index, pr, query, top_k=10):
    words = tokenize(query)
    if not words:
        return []
    cand = index.intersect(words)
    bm = bm25(index, words, cand)
    fs = final_score(bm, pr)
    ranked = sorted(fs.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [(doc, score, snippet(index.docs[doc]["text"], words))
            for doc, score in ranked]


def snippet(text, words, width=30):
    toks = text.split()
    low = [t.lower() for t in toks]
    q = set(words)
    best, best_n = 0, -1
    for i in range(max(1, len(toks) - width)):
        n = sum(1 for t in low[i:i + width] if t.strip(".,;:!?\"'()") in q)
        if n > best_n:
            best, best_n = i, n
    win = toks[best:best + width]
    out = []
    for t in win:
        core = t.lower().strip(".,;:!?\"'()")
        out.append(f"<b>{t}</b>" if core in q else t)
    return " ".join(out) + " …"
