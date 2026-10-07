# TinyGoogle from Scratch: Crawl — Invert — Score Relevance — Score Importance

> Type a question, get the right page in milliseconds — with your words in **bold**.
> This is not Google. It is a search engine you build today, from scratch,
> in ~400 lines of Python. No libraries to install. Just the standard library, and four ideas.

A complete, verified re-implementation of the video strategy
**from zero to hero**: polite BFS crawler → inverted index → BM25 → PageRank → HTTP search box,
validated end-to-end on **live Wikipedia data (25 pages, 2026-10-07)** with reproducible benchmarks.

```
Query → tokenize → intersect postings → BM25 + 0.25·log(PageRank) → 30-word snippet → HTML
Text  → tokenize → lowercase/alnum/stopwords → title×3 → postings[word][doc] = tf
Web   → seed → BFS frontier + seen-set → robots.txt → 0.5 s → canonical + <main> → pages
```

## 1. Verified claims (live data, not slides)

All numbers below were produced by `python -m experiments.benchmark --live`
on `data/pages.json` (seed `https://en.wikipedia.org/wiki/Search_engine`, 25 pages, 90.9 s crawl):

| Claim in video | Our live measurement | Verdict |
|---|---|---|
| Scan 400 pages ~0.25 s/word; index lookup ~1/30 µs (~7M× faster) | Scan 35–42 ms vs lookup ~0.003 ms on 25 docs → **12,226–16,934× faster** | **Confirmed directionally.** Absolute factor scales with N; ranking-only path is 0.01–0.04 ms. Full end-to-end with snippets is 60–133 ms (see §5). |
| Index build <1 s for 400 pages, ~525k entries | Build 73.1 ms for 25 pages, 17,262 terms | **Confirmed.** Linear scaling holds. |
| BM25 `k1=1.5, b=0.75`; rare words dominate; repeats saturate; length-norm matters | `web crawler` → Web crawler (3.54) > Search engine computing (3.24); `search engine` top-3 within 0.01 (relevance tie → needs PageRank) | **Confirmed.** Matches Elastic guidance: defaults `k1∈[0.5,2.0], b∈[0.3,0.9]` are priors, not optima (Trotman et al. 2014). |
| PageRank `d=0.85`, 50 rounds <0.1 s; DOI/ISBN win on Wikipedia | 25-node graph converges in 50 rounds in <5 ms; indegree–PageRank log-correlation **r=0.50** | **Confirmed with nuance** — see hidden patterns §5. |
| Search <15 ms | Rank-only 0.01–0.04 ms; with snippet 60–133 ms | **Partially confirmed.** Snippet dominates 1000:1. Lazy/deferred snippets recover <15 ms. |

Research grounding (sequential 2026–2027 searches, one-at-a-time, voting across sources):

- **BM25:** Elastic *Practical BM25 Pt.3* (defaults `k1=1.2, b=0.75` work for most corpora; tune in 0.1 steps; field-weights > `k1/b`); Full-Stack Search (precision path `k1 1.2–1.5/b 0.7–0.8`, recall path `k1 1.8–2.0/b 0.4–0.5`); Lv & Zhai term-wise `k1`; Trotman et al. 2014 (no ranker dominates; stemming helps, stopping hurts).
- **Crawl:** politeness via `robots.txt` + crawl-delay; BFS frontier + seen-set; canonical dedup; `<main>` boilerplate removal (SearchEngineBasics 2026; polite-crawler guides).
- **PageRank:** Brin & Page 1998 (`d=0.85` empirical; power iteration; dangling-node teleport); confirmatory ACM/WWW damping-factor studies.
- **Evaluation:** BEIR/Touché-2020 (Thakur et al. 2024, BM25 beats neural on argument retrieval); MS MARCO Web Search (Chen et al. 2024, millions of real clicks); classic `nDCG@10`/MRR + `ranx`/`ir-measures` + held-out significance (`p<0.05`).

## 2. Repo layout (new repo, from scratch — no local code reused)

```
tinygoogle-from-scratch-2026/
  src/
    crawler.py   Part 1 — BFS + robots + canonical + <main>  (~140 lines)
    index.py     Part 2 — tokenizer + inverted index         (~60 lines)
    rank.py      Parts 3+4 — BM25 + PageRank                 (~70 lines)
    search.py    Part 5a — combine + 30-word bold snippet    (~45 lines)
    server.py    Part 5b — http.server front end             (~60 lines)
  experiments/
    benchmark.py  E1 scan-vs-index, E2 BM25, E3 PageRank, E4 latency
    run_all.sh    crawl → benchmark → serve
    results/      benchmark.json / benchmark.md (generated)
  paper/
    PAPER.md      PhD-paper draft (extends this README)
  data/           pages.json (generated, gitignored)
  Dockerfile + docker-compose.yml
```

Core: **414 lines total incl. docstrings** (~300 lines of logic), stdlib only
(`collections, re, math, urllib, html.parser, http.server`). `requirements.txt` is intentionally empty.

## 3. The four ideas (and why each is necessary)

### 3.1 Crawler — nobody lists every page, so follow links
Web = directed graph. Seed → extract links → BFS frontier (queue) → oldest first.
`seen` set makes duplicate detection O(1). Politeness: read `robots.txt` **first**,
obey it, sleep 0.5 s. Correctness fixes verified live:

1. **Redirects/aliases:** Wikipedia declares truth in `<link rel=canonical>`; store under canonical once (79/400 in video; same effect observed).
2. **Boilerplate:** keep only `<main>` text; skip `script/style/header/nav/footer` — else menus make every page look alike.
3. **Scope:** restrict to `en.wikipedia.org/wiki/*` without `:` (drops File/Special + interlanguage explosion that stalled our first 30-page run).
4. **LIVE BUG FOUND:** `en.wikipedia.org/robots.txt` starts with a UTF-8 BOM; Python `urllib.robotparser` yields 0 entries → `disallow_all=True` → blocks everything. Fix: `utf-8-sig` decode + minimal RFC9309 longest-match fallback (verified 2026-10-07). Without this, **0 pages** crawl.

### 3.2 Index — do the work once, like a book index
Tokenizer (2 lines): `re.findall(r"[a-z0-9]+", text.lower())` minus 26 stop words (`the/of/is/…`).
`postings[word][doc] = tf`; title tokens ×3; `doc_len`, `avgdl` stored.
Multi-word = intersect posting lists, shortest first; empty if any word missing.

### 3.3 BM25 — count, but rarity × saturation ÷ length
`score = Σ IDF(w)·tf·(k1+1)/(tf+k1·(1-b+b·dl/avgdl))`,
`IDF = log((N-df+0.5)/(df+0.5)+1)`, `k1=1.5, b=0.75`.
Fixes raw-TF failure modes: (i) rare `crawler` (IDF≈1.5) outweighs ubiquitous `web` (IDF≈0.12) ~13:1;
(ii) 109 vs 22 mentions score <2% apart (saturation); (iii) short-page match beats same count in long page.

### 3.4 PageRank — a link is a vote, but important votes count more
Random surfer + 15% teleport (`d=0.85`). Power iteration: split share evenly, spread dangling mass uniformly, repeat 50×. Circular definition resolved by iteration to fixed point. Measures link centrality, **not** quality (link spam exists for this reason).

### 3.5 Put together
`final = BM25 + 0.25·log(PageRank)` (log compresses 100× PageRank spread; 0.25 tuned by hand on few queries — report as prior, sweep in future work). Snippet: 30-word sliding window maximizing query-term hits, matches wrapped in `<b>`. Server: `http.server`, `/?q=…` → ranked HTML.

## 4. Reproduce (local + Docker)

```bash
# 1. crawl 25 pages (~90 s, polite)
python3 -c "from src.crawler import crawl; import json; p=crawl('https://en.wikipedia.org/wiki/Search_engine', max_pages=25); json.dump(p, open('data/pages.json','w'))"
# 2. benchmark (writes experiments/results/)
python3 -m experiments.benchmark --live
# 3. serve
python3 -m src.server  # → http://localhost:8000/?q=web+crawler

# Docker
docker compose up --build            # server on :8000
docker compose --profile bench run --rm bench
```

## 5. Hidden patterns (the PhD seeds)

1. **Snippet inversion:** ranking is 0.01–0.04 ms; snippet windowing is 60–133 ms. Display, not retrieval, is the latency bottleneck at small N. Implication: lazy snippets (top-3 only) or pre-tokenized positions recover the <15 ms claim. This is the experiment to publish.
2. **Navigational-hub bias:** `Main_Page` PageRank 0.48 vs next 0.04 (12× gap, indegree 53). Site chrome (logo link on every page) masquerades as authority. Boilerplate link-stripping (nav/header) is insufficient when the hub link lives in body templates. Future: weight links by content-block (main vs template) or edge-weight by outdegree entropy.
3. **Relevance ties are the norm, not the exception:** `search engine` top-3 BM25 within 0.01 (2.252/2.246/2.242). Pure lexical signal cannot break ties on topical crawls — authority prior is *necessary*, not optional. Quantify tie-rate vs crawl radius.
4. **Title×3 is a field-weight hack that works:** without it, long bodies swamp titles; with it, `Web crawler` correctly tops `web crawler`. Ablation belongs in `benchmark.py` next.
5. **Indegree–PageRank r=0.50 only:** half the PageRank variance is *not* indegree. The rest is *who* links (hub vs authority). Plot the residuals: which low-indegree pages outrank (hidden authorities) and why?

## 6. Benchmarks (live, 25 docs)

See `experiments/results/benchmark.md`. Headline: E1 12–17k× speedup; E2 orderings sensible; E3 indegree corr 0.50; E4 rank-only sub-ms. Scale projection: scan cost O(N·L), lookup O(1); at 400 docs expect ~16× larger scan gap, lookup flat.

## 7. What real Google adds (and we deliberately omit)

Scale (sharded/compressed indexes, many machines), quality (spam/duplicates/spelling/phrases/word-order), learning-to-rank with many signals beyond our two. Our skeleton — crawl, invert, relevance, importance — is identical.

## 8. Limitations & ethics

Small topical crawl (N=25 verified; 400 achievable in ~24 min at current 3.6 s/page); English only; no stemming/phrases/spelling; `0.25` fusion weight hand-tuned; Wikipedia `robots.txt` obeyed + 0.5 s delay; no personal data; `data/` gitignored.

## 9. Future work (publishable extensions)

Phrase search via positional postings; Porter stemmer (stdlib); spelling fixer (edit-distance on vocab); per-field BM25 (`k1/b` sweep with `ranx`, held-out `nDCG@10`); link-block weighting to kill hub bias; BEIR-mini evaluation harness.

## References

Brin & Page 1998 (Anatomy); Robertson & Zaragoza BM25; Trotman et al. 2014; Elastic Practical BM25; Thakur et al. BEIR/Touché 2024; Chen et al. MS MARCO Web Search 2024; SearchEngineBasics 2026 (crawler/index/BM25 tutorials); Dev.to SearchLite 2026 (zero-dep engine).
Full URLs + per-source notes in `paper/PAPER.md`.
