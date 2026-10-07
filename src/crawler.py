"""Part 1 — Polite BFS crawler (stdlib only)."""
import collections
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

AGENT = "TinyGoogle/1.0 (course-project; polite 0.5s)"
DELAY = 0.5


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.skip = 0
        self.text = []
        self.title = ""
        self._in_title = False
        self.canonical = ""
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.in_main = True
        if tag in ("script", "style", "header", "nav", "footer"):
            self.skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "link" and a.get("rel") == "canonical" and a.get("href"):
            self.canonical = a["href"]
        if tag == "a" and "href" in a:
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False
        if tag in ("script", "style", "header", "nav", "footer"):
            self.skip = max(0, self.skip - 1)
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self.in_main and self.skip == 0:
            s = data.strip()
            if s:
                self.text.append(s)


def _manual_robots_allows(robots_text, agent, path):
    """Minimal RFC9309 matcher: longest path wins. Used as fallback."""
    agent = agent.lower()
    groups = []
    cur_agents, cur_rules = [], []
    for raw in robots_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if cur_rules or (cur_agents and cur_agents[-1:]):
                # new group starts when rules already collected
                if cur_rules:
                    groups.append((cur_agents, cur_rules))
                    cur_agents, cur_rules = [], []
            cur_agents.append(v.lower())
        elif k in ("disallow", "allow") and cur_agents:
            if v == "":
                continue  # empty Disallow = allow all
            cur_rules.append((k == "allow", v))
    if cur_agents:
        groups.append((cur_agents, cur_rules))
    # pick groups matching our token or *
    token = agent.split("/")[0]
    best, best_len = [], -1
    for agents, rules in groups:
        for a in agents:
            a = a.strip()
            if a == "*":
                ln = 1
            elif a in agent or token.startswith(a) or a.startswith(token):
                ln = len(a)
            else:
                continue
            if ln > best_len:
                best, best_len = rules, ln
    if best_len == -1:
        return True
    winner = None
    for allow, p in best:
        if path.startswith(p):
            if winner is None or len(p) > len(winner[1]):
                winner = (allow, p)
    if winner is None:
        return True
    return winner[0]


def can_fetch(rp_cache, url):
    try:
        p = urllib.parse.urlparse(url)
        host = f"{p.scheme}://{p.netloc}"
        if host not in rp_cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(host + "/robots.txt")
            try:
                rp.read()
            except Exception:
                rp_cache[host] = None
                return True
            # VERIFIED LIVE 2026-10-07: en.wikipedia robots.txt starts with
            # BOM; stdlib parser yields 0 entries -> disallow_all -> blocks
            # everything. Fall back to manual matcher in that case.
            if len(getattr(rp, "entries", []) or []) == 0:
                try:
                    req = urllib.request.Request(
                        host + "/robots.txt", headers={"User-Agent": AGENT})
                    with urllib.request.urlopen(req, timeout=15) as r:
                        txt = r.read().decode("utf-8-sig", "ignore")
                    rp_cache[host] = ("manual", txt)
                    return _manual_robots_allows(txt, AGENT, p.path or "/")
                except Exception:
                    rp_cache[host] = None
                    return True
            rp_cache[host] = rp
        cached = rp_cache[host]
        if cached is None:
            return True
        if isinstance(cached, tuple) and cached[0] == "manual":
            return _manual_robots_allows(cached[1], AGENT, p.path or "/")
        return cached.can_fetch(AGENT, url)
    except Exception:
        return False


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        final = r.geturl()
        ctype = r.headers.get("Content-Type", "")
        if "html" not in ctype and ctype:
            return None
        return final, r.read().decode("utf-8", "ignore")


def normalize_link(base, href):
    if not href or href.startswith(("#", "javascript:", "mailto:")):
        return ""
    u = urllib.parse.urljoin(base, href)
    p = urllib.parse.urlparse(u)
    if p.netloc != "en.wikipedia.org":
        return ""
    # keep only /wiki/ articles, drop files/special
    if not p.path.startswith("/wiki/") or ":" in p.path:
        return ""
    return urllib.parse.urldefrag(u)[0]


def crawl(seed, max_pages=400):
    frontier = collections.deque([seed])
    seen = {seed}
    pages = {}   # canonical_url -> {url,title,text,links}
    rp_cache = {}
    while frontier and len(pages) >= 0 and len(pages) < max_pages:
        url = frontier.popleft()
        if not can_fetch(rp_cache, url):
            continue
        try:
            got = fetch(url)
            time.sleep(DELAY)
            if not got:
                continue
            final_url, html = got
            ps = PageParser()
            ps.feed(html)
            addr = ps.canonical or final_url
            addr = urllib.parse.urldefrag(addr)[0]
            if addr in pages:
                continue
            out_links = []
            for h in ps.links:
                n = normalize_link(final_url, h)
                if n and n not in seen:
                    seen.add(n)
                    frontier.append(n)
                if n:
                    out_links.append(n)
            pages[addr] = {
                "url": addr,
                "title": ps.title.strip(),
                "text": " ".join(ps.text),
                "links": out_links,
            }
        except Exception:
            continue
    return pages


if __name__ == "__main__":
    import json
    seed = "https://en.wikipedia.org/wiki/Search_engine"
    pages = crawl(seed, max_pages=400)
    with open("data/pages.json", "w") as f:
        json.dump(pages, f)
    print(f"crawled={len(pages)}")
