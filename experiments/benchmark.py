"""Live verification: scan-vs-index, BM25 ablation, PageRank, latency.

Run: python -m experiments.benchmark [--data data/pages.json] [--live]
Writes JSON + markdown tables to experiments/results/.
Stdlib only.
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.index import Index, tokenize
from src.rank import bm25, pagerank

QUERIES = ["web crawler", "search engine", "larry page stanford",
           "google", "pagerank", "wikipedia"]


def load_pages(path):
    with open(path) as f:
        return json.load(f)


def scan(pages, word):
    n = 0
    hits = []
    for u, p in pages.items():
        toks = tokenize(p.get("title", "") + " " + p.get("text", ""))
        c = toks.count(word)
        if c:
            hits.append((u, c))
            n += 1
    return hits


def main():
    data = "data/pages.json"
    live = "--live" in sys.argv
    for a in sys.argv[1:]:
        if a.endswith(".json"):
            data = a
    base = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(base, exist_ok=True)

    if not os.path.exists(data):
        print(f"missing {data}; run a mini-crawl first (see run_all.sh).")
        if not live:
            return
    pages = load_pages(data)
    idx = Index()
    t0 = time.perf_counter()
    idx.build(pages)
    build_ms = (time.perf_counter() - t0) * 1000
    pr = pagerank(pages)

    # E1: scan vs inverted lookup
    e1 = []
    for q in ["crawler", "web"]:
        t0 = time.perf_counter()
        s = scan(pages, q)
        scan_ms = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        post = idx.lookup(q)
        look_ms = (time.perf_counter() - t0) * 1000 + 1e-9
        e1.append({"term": q, "docs": len(post), "scan_ms": round(scan_ms, 3),
                   "lookup_ms": round(look_ms, 6),
                   "speedup": round(scan_ms / look_ms, 1)})

    # E2: BM25 qualitative ordering + ablation (title weight, length norm)
    e2 = []
    for q in QUERIES:
        words = tokenize(q)
        cand = idx.intersect(words)
        full = bm25(idx, words, cand)
        top = sorted(full.items(), key=lambda x: x[1], reverse=True)[:3]
        e2.append({"query": q, "candidates": len(cand),
                   "top3": [(idx.docs[u]["title"][:60], round(s, 3)) for u, s in top]})

    # E3: PageRank hidden pattern — reference infrastructure wins
    top_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:10]
    indeg = {}
    for u, p in pages.items():
        for v in p.get("links", []):
            if v in pages:
                indeg[v] = indeg.get(v, 0) + 1
    e3 = [{"title": pages[u]["title"][:60], "url": u,
           "pagerank": round(r, 6), "indegree": indeg.get(u, 0)}
          for u, r in top_pr]
    # correlation log(indeg+1) vs pagerank
    xs, ys = [], []
    for u, r in pr.items():
        xs.append(math.log(indeg.get(u, 0) + 1))
        ys.append(r)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs) or 1e-12
    vy = sum((b - my) ** 2 for b in ys) or 1e-12
    corr = cov / math.sqrt(vx * vy)

    # E4: end-to-end latency (<15ms claim)
    from src.search import search
    e4 = []
    for q in QUERIES:
        t0 = time.perf_counter()
        hits = search(idx, pr, q)
        ms = (time.perf_counter() - t0) * 1000
        e4.append({"query": q, "hits": len(hits), "ms": round(ms, 3)})

    out = {"docs": len(pages), "terms": len(idx.postings),
           "build_ms": round(build_ms, 1),
           "E1_scan_vs_index": e1, "E2_bm25": e2,
           "E3_pagerank_top10": e3, "pagerank_indegree_corr": round(corr, 3),
           "E4_latency": e4}
    with open(os.path.join(base, "benchmark.json"), "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(base, "benchmark.md"), "w") as f:
        f.write(f"# Benchmark — {out['docs']} docs, {out['terms']} terms\n\n")
        f.write(f"Index build: {out['build_ms']} ms\n\n")
        f.write("## E1 scan vs index\n")
        for r in e1:
            f.write(f"- `{r['term']}`: scan {r['scan_ms']} ms vs lookup "
                    f"{r['lookup_ms']} ms → **{r['speedup']}x**\n")
        f.write("\n## E2 BM25 top-3\n")
        for r in e2:
            f.write(f"- `{r['query']}` ({r['candidates']} cand): {r['top3']}\n")
        f.write(f"\n## E3 PageRank (indeg corr={out['pagerank_indegree_corr']})\n")
        for r in e3:
            f.write(f"- {r['title']} pr={r['pagerank']} indeg={r['indegree']}\n")
        f.write("\n## E4 latency\n")
        for r in e4:
            f.write(f"- `{r['query']}`: {r['hits']} hits in {r['ms']} ms\n")
    print(json.dumps(out, indent=2)[:3000])


if __name__ == "__main__":
    main()
