#!/usr/bin/env python
"""Usage: python scripts/explain_score.py "algorithm complexity" Catalytic_computing Computer_science

Breaks down the BM25 score for specific documents against a query,
term by term, so you can see exactly why one document outranks another
instead of just trusting the final number.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search_engine.query.rank import idf, tf_component
from search_engine.storage.reader import IndexReader
from search_engine.tokenizer.tokenizer import tokenize


def main(query_text: str, doc_titles: list[str]):
    reader = IndexReader(
        "data/index/index.postings",
        "data/index/index.dict",
        meta_path="data/index/index.meta",
    )

    # doc_metadata maps doc_id -> {"title": ..., "path": ...}; build the
    # reverse lookup (title -> doc_id) so callers can pass titles.
    title_to_id = {meta["title"]: doc_id for doc_id, meta in reader.doc_metadata.items()}

    terms = tokenize(query_text)
    print(f"Query: {query_text!r} -> terms: {terms}")
    print(f"Corpus: {reader.num_docs} docs, avg doc length: {reader.avg_doc_len:.1f} terms\n")

    for title in doc_titles:
        doc_id = title_to_id.get(title)
        if doc_id is None:
            print(f"'{title}' not found in index (check exact filename, no .txt)\n")
            continue

        doc_len = reader.doc_lengths[doc_id]
        print(f"--- {title} (doc_id={doc_id}, length={doc_len} terms) ---")

        total = 0.0
        for term in terms:
            postings = reader.get_postings(term)
            doc_freq = len(postings)
            posting = next((p for p in postings if p.doc_id == doc_id), None)

            if posting is None:
                print(f"  '{term}': not present in this doc (df={doc_freq})")
                continue

            term_idf = idf(reader.num_docs, doc_freq)
            term_tf_component = tf_component(posting.term_freq, doc_len, reader.avg_doc_len)
            contribution = term_idf * term_tf_component
            total += contribution

            print(
                f"  '{term}': tf={posting.term_freq}, df={doc_freq}, "
                f"idf={term_idf:.3f}, tf_component={term_tf_component:.3f}, "
                f"contribution={contribution:.3f}"
            )

        print(f"  TOTAL BM25 SCORE: {total:.4f}\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python scripts/explain_score.py "query" doc_title_1 [doc_title_2 ...]')
        print("(doc titles are the .txt filenames without extension, as shown by search.py)")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2:])
