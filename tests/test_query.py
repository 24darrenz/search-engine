from search_engine.index.builder import IndexBuilder
from search_engine.query.boolean import and_query, or_query


def build_toy_index():
    builder = IndexBuilder()
    builder.add_document(0, "python search engine")
    builder.add_document(1, "python machine learning")
    builder.add_document(2, "search engine optimization")
    return builder.finalize()


def test_and_query_intersects():
    index = build_toy_index()
    assert and_query(index, ["python", "search"]) == [0]


def test_or_query_unions():
    index = build_toy_index()
    assert or_query(index, ["python", "optimization"]) == [0, 1, 2]


def test_and_query_missing_term_returns_empty():
    index = build_toy_index()
    assert and_query(index, ["python", "nonexistent"]) == []
