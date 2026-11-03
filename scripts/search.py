#!/usr/bin/env python
"""Usage: python scripts/search.py "operating systems"

Runs a multi-term AND query against the on-disk index, ranks matches by
BM25, and caches results so repeated queries are near-instant.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search_engine.engine import SearchEngine, timed_search


def main(query_text: str):
    engine = SearchEngine(
        "data/index/index.postings",
        "data/index/index.dict",
        "data/index/index.meta",
    )

    # Run twice to demonstrate the cache: first is a real query, second
    # should hit the cache and be much faster.
    ranked, was_hit, elapsed_ms = timed_search(engine, query_text)
    print(f"Query: {query_text!r} -> {len(ranked)} results ({elapsed_ms:.3f} ms, cache hit={was_hit})")
    for doc_id, score in ranked[:10]:
        print(f"  {score:.4f}  {engine.title_for(doc_id)}")

    ranked2, was_hit2, elapsed_ms2 = timed_search(engine, query_text)
    print(f"\nRepeated query -> {elapsed_ms2:.3f} ms (cache hit={was_hit2})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python scripts/search.py "query terms"')
        sys.exit(1)
    main(" ".join(sys.argv[1:]))
