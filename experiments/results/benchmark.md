# Benchmark — 25 docs, 17262 terms

Index build: 73.1 ms

## E1 scan vs index
- `crawler`: scan 41.846 ms vs lookup 0.002471 ms → **16934.8x**
- `web`: scan 35.126 ms vs lookup 0.002873 ms → **12226.1x**

## E2 BM25 top-3
- `web crawler` (7 cand): [('Web crawler - Wikipedia', 3.538), ('Search engine (computing) - Wikipedia', 3.239), ('Search engine - Wikipedia', 3.116)]
- `search engine` (15 cand): [('Search engine - Wikipedia', 2.252), ('Search engine (computing) - Wikipedia', 2.246), ('Search engine results page - Wikipedia', 2.242)]
- `larry page stanford` (4 cand): [('Search engine - Wikipedia', 4.822), ('Google Search - Wikipedia', 4.121), ('Web crawler - Wikipedia', 4.119)]
- `google` (17 cand): [('Google Search - Wikipedia', 0.985), ('Search engine results page - Wikipedia', 0.97), ('Search engine - Wikipedia', 0.962)]
- `pagerank` (6 cand): [('Web crawler - Wikipedia', 3.016), ('Google Search - Wikipedia', 2.768), ('Search engine (computing) - Wikipedia', 2.712)]
- `wikipedia` (25 cand): [('Wikipedia, the free encyclopedia', 0.047), ('Hyperlink - Wikipedia', 0.046), ('Search engine (computing) - Wikipedia', 0.045)]

## E3 PageRank (indeg corr=0.5)
- Wikipedia, the free encyclopedia pr=0.480806 indeg=53
- World Wide Web - Wikipedia pr=0.040759 indeg=34
- Internet - Wikipedia pr=0.040432 indeg=35
- Web page - Wikipedia pr=0.038228 indeg=31
- Web browser - Wikipedia pr=0.03622 indeg=30
- Hyperlink - Wikipedia pr=0.027359 indeg=21
- Computer file - Wikipedia pr=0.027051 indeg=13
- Database - Wikipedia pr=0.026992 indeg=23
- Video - Wikipedia pr=0.023514 indeg=8
- Web crawler - Wikipedia pr=0.02339 indeg=21

## E4 latency
- `web crawler`: 7 hits in 103.17 ms
- `search engine`: 10 hits in 115.548 ms
- `larry page stanford`: 4 hits in 96.882 ms
- `google`: 10 hits in 132.267 ms
- `pagerank`: 6 hits in 62.042 ms
- `wikipedia`: 10 hits in 123.906 ms
