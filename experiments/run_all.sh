#!/bin/bash
# End-to-end reproduction: crawl -> benchmark -> serve
set -e
cd "$(dirname "$0")/.."
echo "[1/3] crawl 25 pages (polite 0.5s, ~90s)..."
python3 -c "from src.crawler import crawl; import json; p=crawl('https://en.wikipedia.org/wiki/Search_engine', max_pages=25); json.dump(p, open('data/pages.json','w')); print('crawled', len(p))"
echo "[2/3] benchmark..."
python3 -m experiments.benchmark --live
cat experiments/results/benchmark.md
echo "[3/3] serve on :8000 (Ctrl-C to stop)..."
python3 -m src.server
