#!/usr/bin/env python
"""Benchmark: linear scan vs. inverted index vs. inverted index + cache.

Usage:
    python benchmarks/bench_query_latency.py "process scheduling" "operating system"

Requires an index already built at data/index/ (run scripts/build_index.py
first) and the original .txt corpus still present at data/raw/ (needed
only for the linear-scan baseline, which re-reads the raw text).
"""
import sys
import time
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search_engine.engine import SearchEngine
from search_engine.tokenizer.tokenizer import tokenize

REPEATS = 20


def load_corpus(raw_dir: str) -> list[str]:
    texts = []
    for path in sorted(Path(raw_dir).glob("*.txt")):
        texts.append(path.read_text(errors="ignore"))
    return texts


def linear_scan(corpus: list[str], terms: list[str]) -> list[int]:
    """Naive baseline: tokenize every document at query time and check
    all query terms are present. This is what you'd do with no index at
    all -- it's the "before" number in the story."""
    results = []
    for doc_id, text in enumerate(corpus):
        doc_terms = set(tokenize(text))
        if all(t in doc_terms for t in terms):
            results.append(doc_id)
    return results


def time_it(fn, repeats: int = REPEATS) -> float:
    """Average wall-clock time per call, in milliseconds."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)
    return mean(times)


def main(queries: list[str]):
    corpus = load_corpus("data/raw")
    print(f"Corpus size: {len(corpus)} documents\n")

    engine = SearchEngine(
        "data/index/index.postings",
        "data/index/index.dict",
        "data/index/index.meta",
    )

    rows = []
    for query in queries:
        terms = tokenize(query)

        linear_ms = time_it(lambda: linear_scan(corpus, terms))

        # Fresh cache per query so "inverted index" (no cache) is measured
        # honestly rather than accidentally hitting a warm cache.
        engine.cache = engine.cache.__class__(capacity=engine.cache.capacity)
        indexed_ms = time_it(lambda: engine.search(query, use_cache=False))

        # Warm the cache once, then time repeated hits.
        engine.search(query, use_cache=True)
        cached_ms = time_it(lambda: engine.search(query, use_cache=True))

        rows.append((query, linear_ms, indexed_ms, cached_ms))

    header = f"{'Query':30} {'Linear scan':>14} {'Inverted idx':>14} {'+ cache':>10}"
    print(header)
    print("-" * len(header))
    for query, linear_ms, indexed_ms, cached_ms in rows:
        print(f"{query:30} {linear_ms:>11.3f} ms {indexed_ms:>11.3f} ms {cached_ms:>7.3f} ms")


if __name__ == "__main__":
    queries = sys.argv[1:] or ["process scheduling", "operating system"]
    main(queries)
