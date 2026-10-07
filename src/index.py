"""Part 2 — Tokenizer + inverted index (stdlib only)."""
import re

STOP = {
    "a", "about", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "how", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "which", "with",
}

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text):
    """lowercase, split on non-alnum, drop stop words. 2 lines of logic."""
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


class Index:
    def __init__(self):
        self.postings = {}   # word -> {doc: count}
        self.doc_len = {}    # doc -> token count
        self.docs = {}       # doc -> page dict

    def add(self, doc_id, title, text):
        toks = tokenize(title) * 3 + tokenize(text)  # title counts 3x
        self.docs[doc_id] = {"title": title, "text": text}
        self.doc_len[doc_id] = len(toks)
        counts = {}
        for t in toks:
            counts[t] = counts.get(t, 0) + 1
        for t, c in counts.items():
            self.postings.setdefault(t, {})[doc_id] = c

    def build(self, pages):
        for url, p in pages.items():
            self.add(url, p.get("title", ""), p.get("text", ""))

    @property
    def avgdl(self):
        n = len(self.doc_len)
        return sum(self.doc_len.values()) / n if n else 0.0

    def lookup(self, word):
        return self.postings.get(word, {})

    def intersect(self, words):
        """Pages containing EVERY word; start from shortest posting list."""
        lists = [self.lookup(w) for w in words]
        if any(len(x) == 0 for x in lists):
            return set()
        lists.sort(key=len)
        out = set(lists[0])
        for lst in lists[1:]:
            out &= set(lst)
            if not out:
                break
        return out
