"""Ties together the reader, boolean query processing, and BM25 ranking
behind a query result cache.

This is the object scripts/search.py (and, later, an API layer) should
call into, rather than each caller re-implementing the "tokenize -> fetch
postings -> and_query -> rank -> cache" sequence by hand.
"""
import json
import time

from search_engine.query.boolean import and_query
from search_engine.query.rank import rank_documents
from search_engine.storage.reader import IndexReader
from search_engine.tokenizer.tokenizer import tokenize
from search_engine.cache import LRUCache


class SearchEngine:
    def __init__(
        self,
        postings_path: str,
        dict_path: str,
        meta_path: str,
        cache_capacity: int = 256,
    ):
        self.reader = IndexReader(postings_path, dict_path, meta_path=meta_path)
        self.cache = LRUCache(capacity=cache_capacity)

    def _cache_key(self, query_text: str) -> str:
        # Normalize so "Search Engine" and "search engine" share a cache
        # entry -- the tokenizer already lowercases, so re-derive the key
        # from the tokenized terms rather than the raw query string.
        terms = tokenize(query_text)
        return json.dumps(terms)

    def search(self, query_text: str, use_cache: bool = True) -> tuple[list[tuple[int, float]], bool]:
        """Returns (ranked_results, was_cache_hit)."""
        key = self._cache_key(query_text)

        if use_cache:
            cached = self.cache.get(key)
            if cached is not None:
                return cached, True

        terms = tokenize(query_text)
        index_view = {t: self.reader.get_postings(t) for t in terms}
        doc_ids = and_query(index_view, terms)
        ranked = rank_documents(
            doc_ids,
            terms,
            index_view,
            self.reader.doc_lengths,
            self.reader.avg_doc_len,
            self.reader.num_docs,
        )

        if use_cache:
            self.cache.put(key, ranked)

        return ranked, False

    def title_for(self, doc_id: int) -> str:
        return self.reader.doc_metadata.get(doc_id, {}).get("title", f"doc {doc_id}")


def timed_search(engine: SearchEngine, query_text: str, use_cache: bool = True):
    start = time.perf_counter()
    ranked, was_hit = engine.search(query_text, use_cache=use_cache)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return ranked, was_hit, elapsed_ms
