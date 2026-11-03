import tempfile
from pathlib import Path

from search_engine.index.builder import IndexBuilder
from search_engine.storage.writer import write_index
from search_engine.engine import SearchEngine


def build_temp_index(tmpdir: Path):
    builder = IndexBuilder()
    builder.add_document(0, "process scheduling operating system", {"title": "os1"})
    builder.add_document(1, "process scheduling algorithms explained", {"title": "os2"})
    builder.add_document(2, "chocolate cake recipe", {"title": "cake"})
    index = builder.finalize()

    postings_path = tmpdir / "index.postings"
    dict_path = tmpdir / "index.dict"
    meta_path = tmpdir / "index.meta"
    write_index(
        index,
        str(postings_path),
        str(dict_path),
        doc_lengths=builder.doc_lengths,
        doc_metadata=builder.doc_metadata,
        meta_path=str(meta_path),
    )
    return postings_path, dict_path, meta_path


def test_search_returns_ranked_results():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        postings_path, dict_path, meta_path = build_temp_index(tmpdir)
        engine = SearchEngine(str(postings_path), str(dict_path), str(meta_path))

        ranked, was_hit = engine.search("process scheduling")
        doc_ids = [doc_id for doc_id, _ in ranked]

        assert not was_hit
        assert 0 in doc_ids and 1 in doc_ids
        assert 2 not in doc_ids  # cake doc shouldn't match


def test_repeated_query_hits_cache():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        postings_path, dict_path, meta_path = build_temp_index(tmpdir)
        engine = SearchEngine(str(postings_path), str(dict_path), str(meta_path))

        _, was_hit_first = engine.search("process scheduling")
        _, was_hit_second = engine.search("process scheduling")

        assert not was_hit_first
        assert was_hit_second


def test_case_insensitive_queries_share_cache_entry():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        postings_path, dict_path, meta_path = build_temp_index(tmpdir)
        engine = SearchEngine(str(postings_path), str(dict_path), str(meta_path))

        engine.search("Process Scheduling")
        _, was_hit = engine.search("process scheduling")

        assert was_hit
