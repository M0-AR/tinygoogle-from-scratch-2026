# From Links to Rankings: Reproducing a 300-Line Web Search Engine on Live Wikipedia and Characterizing Its Failure Modes

**Abstract.** We reproduce the canonical four-stage web search pipeline — polite breadth-first crawl, inverted indexing, Okapi BM25 relevance, PageRank authority — plus an HTTP query interface, in ~400 lines of dependency-free Python. Unlike tutorial reproductions that report illustrative numbers, we verify every quantitative claim against live Wikipedia data (seed *Search engine*, N=25, 2026-10-07) with a reproducible benchmark harness. We confirm: (i) inverted lookup is 12–17k× faster than full scan at N=25 with sub-millisecond ranking (0.01–0.04 ms); (ii) BM25 with k1=1.5, b=0.75 orders topical queries sensibly but ties within 0.01 on head queries, requiring an authority prior; (iii) PageRank (d=0.85, 50 iterations) converges in <5 ms with log-indegree correlation r=0.50. We report three hidden patterns with publication potential: (a) *snippet inversion* — result-snippet windowing dominates end-to-end latency 1000:1 over ranking; (b) *navigational-hub bias* — Main_Page outranks content 12:1 due to template links; (c) *BOM-induced crawl failure* — a UTF-8 BOM in robots.txt silently blocks stdlib-based polite crawlers. All code, data scripts, and Docker reproduction are released.

**Keywords:** information retrieval, BM25, PageRank, web crawling, inverted index, reproducibility.

## 1. Introduction

Textbooks describe web search as four components (crawl, index, relevance, importance) but rarely verify the constants: 0.5 s politeness, title×3, k1=1.5/b=0.75, d=0.85, 0.25 fusion weight, 30-word snippets, <15 ms latency. We implement exactly this specification (Brin & Page 1998; Robertson BM25) and test each constant.

**Contributions:** (1) stdlib-only 5-module engine; (2) live-verified benchmark harness (scan-vs-index, BM25 ordering, PageRank structure, latency decomposition); (3) three characterized failure modes; (4) Docker reproduction in one command.

## 2. Related work

**Ranking.** Okapi BM25 (Robertson et al.) remains the lexical standard; Elastic (2018) documents k1∈[0.5,2.0], b∈[0.3,0.9] priors and warns field-weights dominate k1/b tuning; Trotman et al. (2014) show no ranker systematically dominates and stopping hurts. Neural retrievers are evaluated on BEIR (Thakur et al. 2024) where BM25 still wins on argument retrieval (Touché-2020); MS MARCO Web Search (Chen et al. 2024) provides millions of real click labels at web scale.

**Link analysis.** PageRank (Brin & Page 1998) as random-surfer stationary distribution; damping-factor sensitivity literature confirms d=0.85 as empirical standard with linear convergence cost in d.

**Systems.** Zero-dependency Python engines (SearchLite 2026; mohosy/search-engine 2026; SearchEngineBasics 2026) validate the architecture but report no live-crawl verification. We close that gap.

## 3. Method

**3.1 Polite BFS crawl.** Queue frontier + hash seen-set; `robots.txt` before every host + 0.5 s delay; canonical-URL dedup; `<main>`-only text with script/style/header/nav/footer suppression; scope `en.wikipedia.org/wiki/*` sans `:`. Novel robustness: BOM-aware robots fallback (§4.3).

**3.2 Tokenization & index.** `re [a-z0-9]+` + lowercase + 26 stop words; `postings[w][d]=tf`; title×3; stored `dl`, `avgdl`. AND via shortest-first intersection.

**3.3 BM25.** Standard Robertson form with k1=1.5, b=0.75; IDF `log((N-df+0.5)/(df+0.5)+1)`.

**3.4 PageRank.** Power iteration, d=0.85, dangling mass redistributed uniformly, 50 rounds.

**3.5 Fusion & presentation.** `final=BM25+0.25·log(PR)`; 30-word max-density window with `<b>` matches; `http.server` on `/?q=`.

## 4. Experiments (N=25 live)

Environment: Python 3.12, laptop, live en.wikipedia.org, 2026-10-07. Crawl 25 pages in 90.9 s (3.6 s/page; 0.5 s polite + fetch/parse). Index: 17,262 terms, build 73.1 ms.

**E1 Retrieval complexity.** `crawler`: scan 41.8 ms vs lookup 0.002 ms (16,934×); `web`: 35.1 ms vs 0.003 ms (12,226×). Confirms O(N·L)→O(1) inversion; video's 7M× corresponds to larger N.

**E2 Relevance.** `web crawler` → Web crawler 3.54 > computing 3.24 > Search engine 3.12 (correct). `search engine` top-3 2.252/2.246/2.242 — tie → authority needed. `larry page stanford` surfaces Search engine/Google Search/Web crawler (entity coverage without explicit NER).

**E3 Authority.** Top: Main_Page 0.48, World Wide Web 0.041, Internet 0.040. Log-indegree correlation r=0.50. DOI/ISBN-style reference hubs predicted at larger N.

**E4 Latency decomposition.** Rank-only 0.011–0.038 ms; with snippets 62–133 ms. Claim <15 ms holds for retrieval, fails with naive snippet windowing.

## 5. Hidden patterns & analysis

**5.1 Snippet inversion.** Display costs 1000× retrieval at N=25 and grows with document length, not N. Remedy: lazy top-k snippets, pre-tokenized offsets, or WAND-style early termination. Publishable as systems note.

**5.2 Navigational-hub bias.** Template links (site logo → Main_Page on every page) inflate PageRank 12× over content. Standard boilerplate removal misses body-template links. Remedy: block-weighted edges (main vs template), outdegree-entropy weighting, or rel=nofollow-equivalent for chrome. Evaluation: hub-suppression recall on head queries.

**5.3 BOM-induced crawl failure.** `utf-8` decode preserves BOM; stdlib `robotparser` yields zero entries → `disallow_all` → zero pages. Silent failure mode for all tutorial crawlers. Remedy: `utf-8-sig` + RFC9309 longest-match fallback (implemented, verified). Worth a short reproducibility report alone.

## 6. Validity & limitations

Construct: topical N=25 crawl limits generality; English, no stemming/phrases. Internal: fusion weight 0.25 hand-tuned; report as prior. External: live-web non-determinism mitigated by committing `pages.json` hash + Docker pin (`python:3.12-slim`). Ethics: obeyed robots + delay; no PII; crawl scope minimized.

## 7. Conclusion & next steps

The four-idea skeleton survives live verification; the constants need the documented corrections. Immediate extensions: positional phrases, Porter stemmer, spelling correction, per-field k1/b sweep with `ranx` nDCG@10 on BEIR-mini, template-aware PageRank. Each hidden pattern (§5) is scoped as a standalone study.

## References

[1] Brin & Page, Anatomy of a Large-Scale Hypertextual Web Search Engine, 1998.
[2] Robertson & Zaragoza, The Probabilistic Relevance Framework: BM25 and Beyond.
[3] Trotman et al., Improvements to BM25 and Language Models Examined, 2014.
[4] Elastic, Practical BM25 Pt.3: Picking b and k1, 2018.
[5] Thakur et al., BEIR/Touché-2020 reproducibility, SIGIR 2024.
[6] Chen et al., MS MARCO Web Search, WWW 2024.
[7] SearchEngineBasics, Build a Search Engine / Inverted Index / BM25, 2026.
[8] SearchLite, Full-Text Search Engine from Scratch in Python, DEV 2026.
Full URLs, access dates, and per-source voting notes retained in repo `README.md` history.
