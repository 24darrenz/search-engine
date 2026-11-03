"""Builds an in-memory inverted index from a corpus.

v1: single-pass, everything held in memory. Fine up to ~100k-1M small docs.
If you later want to discuss handling corpora too big for RAM, this is the
place to add an external-merge / SPIMI-style construction as a stretch goal.
"""
from collections import defaultdict

from search_engine.index.posting import Posting, sort_postings
from search_engine.tokenizer.tokenizer import tokenize


class IndexBuilder:
    def __init__(self):
        self.index: dict[str, list[Posting]] = defaultdict(list)
        self.doc_lengths: dict[int, int] = {}
        self.doc_metadata: dict[int, dict] = {}

    def add_document(self, doc_id: int, text: str, metadata: dict | None = None) -> None:
        tokens = tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)
        self.doc_metadata[doc_id] = metadata or {}

        term_positions: dict[str, list[int]] = defaultdict(list)
        for pos, term in enumerate(tokens):
            term_positions[term].append(pos)

        for term, positions in term_positions.items():
            self.index[term].append(
                Posting(doc_id=doc_id, term_freq=len(positions), positions=positions)
            )

    def finalize(self) -> dict[str, list[Posting]]:
        """Sort each posting list by doc_id. Call once after adding all docs."""
        for term in self.index:
            self.index[term] = sort_postings(self.index[term])
        return self.index
