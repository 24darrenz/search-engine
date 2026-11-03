"""BM25 ranking.

score(doc, query) = sum over query terms of:
    idf(term) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))

k1 controls how quickly extra term occurrences stop mattering (diminishing
returns). b controls how strongly document length is normalized against
the average. 1.5 / 0.75 are the standard textbook defaults.
"""
import math

from search_engine.index.posting import Posting


def idf(num_docs: int, doc_freq: int) -> float:
    """Rare terms (small doc_freq) get a higher weight."""
    return math.log((num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)


def tf_component(
    term_freq: int,
    doc_len: int,
    avg_doc_len: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Saturating term-frequency score, normalized by document length."""
    numerator = term_freq * (k1 + 1)
    denominator = term_freq + k1 * (1 - b + b * doc_len / avg_doc_len)
    return numerator / denominator


def _postings_by_doc_id(postings: list[Posting]) -> dict[int, Posting]:
    return {p.doc_id: p for p in postings}


def bm25_score_for_doc(
    doc_id: int,
    query_terms: list[str],
    index: dict[str, list[Posting]],
    doc_lengths: dict[int, int],
    avg_doc_len: float,
    num_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    score = 0.0
    for term in query_terms:
        postings = index.get(term, [])
        doc_freq = len(postings)
        if doc_freq == 0:
            continue
        # NOTE: O(doc_freq) per term per doc via this lookup. Fine for now;
        # if it shows up in a benchmark as a bottleneck, switch to passing
        # in pre-built {term: {doc_id: Posting}} maps instead of rebuilding
        # this dict on every call.
        posting = _postings_by_doc_id(postings).get(doc_id)
        if posting is None:
            continue
        score += idf(num_docs, doc_freq) * tf_component(
            posting.term_freq, doc_lengths[doc_id], avg_doc_len, k1, b
        )
    return score


def rank_documents(
    candidate_doc_ids: list[int],
    query_terms: list[str],
    index: dict[str, list[Posting]],
    doc_lengths: dict[int, int],
    avg_doc_len: float,
    num_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[tuple[int, float]]:
    """Score and sort candidate docs (e.g. output of and_query/or_query)
    by BM25 relevance, highest first."""
    scored = [
        (
            doc_id,
            bm25_score_for_doc(
                doc_id, query_terms, index, doc_lengths, avg_doc_len, num_docs, k1, b
            ),
        )
        for doc_id in candidate_doc_ids
    ]
    return sorted(scored, key=lambda x: x[1], reverse=True)
