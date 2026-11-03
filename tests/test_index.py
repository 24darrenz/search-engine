from search_engine.index.builder import IndexBuilder


def test_builds_index_over_toy_docs():
    builder = IndexBuilder()
    builder.add_document(0, "the cat sat on the mat")
    builder.add_document(1, "the dog sat on the log")
    index = builder.finalize()

    assert "cat" in index
    assert "dog" in index
    sat_doc_ids = {p.doc_id for p in index["sat"]}
    assert sat_doc_ids == {0, 1}


def test_posting_lists_sorted_by_doc_id():
    builder = IndexBuilder()
    builder.add_document(5, "python")
    builder.add_document(1, "python")
    builder.add_document(3, "python")
    index = builder.finalize()

    doc_ids = [p.doc_id for p in index["python"]]
    assert doc_ids == sorted(doc_ids)
