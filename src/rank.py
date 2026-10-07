"""Part 3+4 — BM25 relevance + PageRank importance (stdlib only)."""
import math

K1 = 1.5
B = 0.75
DAMPING = 0.85


def bm25(index, query_words, candidates=None):
    """Robertson/Sparck-Jones BM25. One loop over words, one over postings."""
    N = len(index.doc_len)
    avgdl = index.avgdl
    scores = {}
    for w in query_words:
        post = index.lookup(w)
        if not post:
            continue
        df = len(post)
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
        for doc, tf in post.items():
            if candidates is not None and doc not in candidates:
                continue
            dl = index.doc_len[doc]
            num = tf * (K1 + 1.0)
            den = tf + K1 * (1.0 - B + B * dl / avgdl)
            scores[doc] = scores.get(doc, 0.0) + idf * num / den
    return scores


def pagerank(pages, rounds=50, d=DAMPING):
    """Power iteration. Dangling nodes spread evenly. ~10 lines of math."""
    urls = list(pages)
    n = len(urls)
    pos = {u: i for i, u in enumerate(urls)}
    out = []
    for u in urls:
        links = [x for x in pages[u].get("links", []) if x in pos]
        out.append(links)
    rank = [1.0 / n] * n
    for _ in range(rounds):
        nxt = [(1.0 - d) / n] * n
        dangling = sum(r for r, o in zip(rank, out) if not o)
        for i in range(n):
            nxt[i] += d * dangling / n
        for i, links in enumerate(out):
            if links:
                share = d * rank[i] / len(links)
                for v in links:
                    nxt[pos[v]] += share
        rank = nxt
    return {u: rank[pos[u]] for u in urls}


def final_score(bm, pr, w=0.25):
    return {d: s + w * math.log(pr.get(d, 1e-12)) for d, s in bm.items()}
