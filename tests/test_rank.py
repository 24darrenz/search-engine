from search_engine.index.builder import IndexBuilder
from search_engine.query.rank import bm25_score_for_doc, idf, rank_documents


def build_toy_index():
    builder = IndexBuilder()
    # "python" is rare (1 doc), "search" is common (appears in all 3)
    builder.add_document(0, "python python python programming language")
    builder.add_document(1, "search engine architecture")
    builder.add_document(2, "search engine ranking search relevance search")
    index = builder.finalize()
    return index, builder.doc_lengths


def test_idf_favors_rarer_terms():
    common_idf = idf(num_docs=100, doc_freq=90)
    rare_idf = idf(num_docs=100, doc_freq=1)
    assert rare_idf > common_idf


def test_doc_with_more_term_occurrences_scores_higher_for_that_term():
    index, doc_lengths = build_toy_index()
    avg_len = sum(doc_lengths.values()) / len(doc_lengths)
    num_docs = len(doc_lengths)

    # doc 2 mentions "search" 3x, doc 1 mentions it once
    score_doc1 = bm25_score_for_doc(1, ["search"], index, doc_lengths, avg_len, num_docs)
    score_doc2 = bm25_score_for_doc(2, ["search"], index, doc_lengths, avg_len, num_docs)
    assert score_doc2 > score_doc1


def test_rank_documents_sorts_descending():
    index, doc_lengths = build_toy_index()
    avg_len = sum(doc_lengths.values()) / len(doc_lengths)
    num_docs = len(doc_lengths)

    ranked = rank_documents([1, 2], ["search"], index, doc_lengths, avg_len, num_docs)
    scores = [score for _, score in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranked[0][0] == 2  # doc 2 has more "search" occurrences
