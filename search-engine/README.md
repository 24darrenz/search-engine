# search-engine

A search engine built from scratch — tokenizer, inverted index, boolean
query processing, BM25 ranking, and a query cache — with no external
search/IR libraries (no Lucene, Elasticsearch, Whoosh, etc.). The goal of
this project was to understand and implement the internals of how search
actually works, not to wrap an existing engine.

## What it does

Given a corpus of plain-text documents, this engine:
1. Tokenizes and normalizes text (lowercasing, punctuation stripping, stopword removal)
2. Builds an inverted index (term → sorted list of documents containing it)
3. Answers multi-term boolean queries (AND / OR) via merge-based posting-list intersection
4. Ranks matching documents by relevance using BM25
5. Caches repeated queries with an LRU cache
6. Persists the index to disk in a compact binary format, so it doesn't need to be rebuilt on every run

## Architecture

```
Documents (.txt)
      │
      ▼
 ┌───────────┐
 │ Tokenizer │  lowercase, strip punctuation, remove stopwords
 └─────┬─────┘
       │
       ▼
┌─────────────────┐
│  Inverted Index  │  term -> sorted list of (doc_id, term_freq) postings
└────────┬─────────┘
         │
   ┌─────▼─────┐
   │  Storage   │  binary postings file + JSON dictionary/metadata,
   │ (disk I/O) │  loaded back via seek+read (no full-file scan)
   └─────┬─────┘
         │
   ┌─────▼─────┐
   │  Boolean   │  AND: merge-intersect sorted posting lists (O(n+m))
   │   Query    │  OR:  merge-union sorted posting lists
   └─────┬─────┘
         │
   ┌─────▼─────┐
   │   BM25     │  ranks the boolean-matched candidate set by relevance
   │  Ranking   │
   └─────┬─────┘
         │
   ┌─────▼─────┐
   │ LRU Cache  │  repeated queries (within one process) skip re-computation
   └─────┬─────┘
         │
         ▼
   Ranked results
```

## Real numbers

Corpus: 142 Wikipedia articles from the Computer Science category tree
(fetched via the MediaWiki API, recursing into subcategories).

**Indexing:**
| Metric | Value |
|---|---|
| Documents indexed | 142 |
| Vocabulary size | 13,004 unique terms |
| Indexing time | 2.89s |

**Query latency** (average over repeated runs; `python benchmarks/bench_query_latency.py`):

| Query | Linear scan | Inverted index | + LRU cache |
|---|---|---|---|
| "algorithm complexity" | 51.12 ms | 0.48 ms | 0.007 ms |
| "data structures" | 51.00 ms | 0.34 ms | 0.004 ms |

The inverted index is roughly **100x faster** than a naive linear scan over
the raw corpus, and the query cache is another **~50-100x faster** on top
of that for repeated queries.

Worth noting: at very small corpus sizes (a handful of documents), linear
scan can actually *beat* the inverted index, since Python-level overhead
(dict construction, function calls) dominates before the corpus is large
enough for "scan everything" to actually be expensive. The inverted
index's advantage grows with corpus size — this is exactly the kind of
crossover you'd expect from Big-O behavior meeting constant-factor reality.

## Design notes / things I'd flag in an interview

- **Posting lists are kept sorted by doc_id.** This is what makes AND/OR
  queries a linear merge-walk (`O(n+m)`) instead of a nested-loop
  comparison (`O(n*m)`), and is also a prerequisite for delta/gap encoding
  if the index were compressed later.
- **The on-disk format is a two-file layout**: a small JSON dictionary
  mapping term -> (byte offset, length), and one large binary postings
  file. Looking up a term's postings is a single seek + read, not a scan
  of the whole file — this is standard practice in real search engines
  and is what lets index size scale independently of per-query cost.
- **The LRU cache is per-process, not persistent.** It lives in memory for
  the lifetime of one `SearchEngine` instance and resets between separate
  script invocations. In a long-running server this would stay warm across
  many requests; in the current CLI, each run starts cold.
- **BM25's length normalization can favor short, focused documents over
  long general ones — verified with a term-by-term breakdown, not just
  assumed.** For the query "algorithm complexity", `Catalytic_computing`
  (315 terms) outranked `Computer_science` (3,016 terms — ~5x the corpus
  average of 608) despite the latter containing more raw occurrences of
  "algorithm" (3 vs. 1). Breaking down the score
  (`scripts/explain_score.py`) shows why: BM25's `tf_component` for
  "algorithm" was 1.277 for the short doc vs. only 0.837 for the long one,
  because the length-normalization term (`b * doc_len / avg_doc_len`)
  scales with how far a document's length exceeds the corpus average —
  at 5x average length, that penalty outweighs having 3x the raw term
  count. This is BM25 behaving exactly as designed (it rewards term
  *concentration*, not just raw count), not a bug — but it's a concrete
  example of why a ranking algorithm's output needs to be verified against
  its actual formula rather than assumed to "just work."

## Project layout

```
search-engine/
├── search_engine/
│   ├── tokenizer/tokenizer.py   # text -> normalized terms
│   ├── index/
│   │   ├── posting.py           # Posting dataclass, sorting
│   │   └── builder.py           # builds the in-memory inverted index
│   ├── query/
│   │   ├── boolean.py           # AND/OR merge-intersection
│   │   └── rank.py              # BM25 scoring
│   ├── storage/
│   │   ├── writer.py            # serialize index to disk (binary + JSON)
│   │   └── reader.py            # load index back via seek+read
│   ├── cache.py                 # LRU query cache
│   └── engine.py                # ties the above together behind SearchEngine
├── scripts/
│   ├── fetch_wikipedia.py       # pull a corpus from the MediaWiki API
│   ├── build_index.py           # CLI: build + persist the index
│   ├── search.py                # CLI: run a ranked, cached query
│   └── explain_score.py         # CLI: term-by-term BM25 score breakdown
│                                 # for two or more docs against a query
├── benchmarks/
│   └── bench_query_latency.py   # linear scan vs. index vs. +cache
├── tests/                       # 14 tests covering tokenizer, index,
│                                 # boolean query, ranking, and caching
└── data/
    ├── raw/                     # input corpus (.txt files)
    └── index/                   # built index (index.dict/.postings/.meta)
```

## Running it

```bash
python -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

# Pull a corpus (recurses into Wikipedia subcategories for enough articles)
python scripts/fetch_wikipedia.py --category "Computer science" --limit 150 --depth 2

# Build the index
python scripts/build_index.py data/raw

# Search
python scripts/search.py "operating system scheduling"

# Benchmark
python benchmarks/bench_query_latency.py "algorithm complexity" "data structures"

# Run tests
pytest
```

## What's intentionally not built

To keep the project focused on core IR/systems concepts rather than web
plumbing, the following were deliberately left out or deprioritized:
- No embeddings / semantic search — the point of this project is classic
  information-retrieval and systems fundamentals, not ML (kept separate
  from other ML-focused portfolio projects).
- No web frontend / REST API — the engine is complete and testable via
  CLI; a thin API layer could be added on top without changing any of the
  above.
- No compressed posting lists (delta/gap encoding) — noted as a natural
  extension given that posting lists are already kept sorted, which is
  the prerequisite for it.
