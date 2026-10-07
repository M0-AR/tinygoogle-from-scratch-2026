"""Part 5b — stdlib HTTP front end: /?q=words -> ranked HTML."""
import html
import json
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from .index import Index
from .rank import pagerank
from .search import search

IDX = Index()
PR = {}


def load(path="data/pages.json"):
    global PR
    with open(path) as f:
        pages = json.load(f)
    IDX.build(pages)
    PR = pagerank(pages)
    print(f"loaded docs={len(IDX.docs)} terms={len(IDX.postings)}")


PAGE = """<html><body><h1>tinygoogle</h1>
<form><input name=q value="{q}" size=60><button>Search</button></form>
<p>{meta}</p>{rows}</body></html>"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        q = qs.get("q", [""])[0]
        t0 = time.perf_counter()
        hits = search(IDX, PR, q) if q else []
        ms = (time.perf_counter() - t0) * 1000
        rows = "".join(
            f"<p><a href='{html.escape(u)}'>{html.escape(IDX.docs[u]['title'])}</a>"
            f" [{s:.2f}]<br>{sn}</p>" for u, s, sn in hits)
        body = PAGE.format(q=html.escape(q),
                           meta=f"{len(hits)} results in {ms:.1f} ms" if q else "",
                           rows=rows)
        b = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


def main(port=8000, data="data/pages.json"):
    load(data)
    HTTPServer(("", port), H).serve_forever()


if __name__ == "__main__":
    main()
